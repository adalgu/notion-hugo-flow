#!/usr/bin/env python3
"""
Notion-Hugo 통합 파이프라인

이 스크립트는 Notion에서 콘텐츠를 가져와 마크다운으로 변환하고,
Hugo 전처리를 통해 오류 파일을 처리한 후 Hugo 빌드를 실행합니다.

실행 방법:
    python -m src.notion_hugo [options]

옵션:
    --notion-only: Notion에서 마크다운 변환만 실행
    --hugo-only: Hugo 전처리 및 빌드만 실행
    --no-build: Hugo 빌드 단계 건너뛰기
    --hugo-args="...": Hugo에 전달할 인자 (예: --hugo-args="server --minify")
"""

import os
import sys
import argparse
import signal
from typing import Dict, List, Any, Optional, Tuple, Set, cast
import json
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

from .config import (
    Config,
    load_config,
    create_config_file,
    DatabaseMount,
    PageMount,
)
from .helpers import iterate_paginated_api, is_full_page, ensure_directory
from typing import Union
from .render import save_page, batch_process_pages
from .file import get_all_content_files
from .types import BatchProcessResult
from .hugo_processor import HugoProcessor
from .notion_setup import NotionSetup, NotionMigration, NotionSetupConfig
from .metadata import MetadataManager


def parse_arguments():
    """
    명령줄 인수를 파싱합니다.

    Returns:
        파싱된 인수
    """
    parser = argparse.ArgumentParser(description="Notion-Hugo 통합 파이프라인")
    # 기존 파이프라인 옵션
    parser.add_argument(
        "--notion-only", action="store_true", help="Notion에서 마크다운 변환만 실행"
    )
    parser.add_argument(
        "--hugo-only", action="store_true", help="Hugo 전처리 및 빌드만 실행"
    )
    parser.add_argument(
        "--no-build", action="store_true", help="Hugo 빌드 단계 건너뛰기"
    )
    parser.add_argument(
        "--hugo-args",
        default="",
        help="Hugo에 전달할 인자 (예: --hugo-args='server --minify')",
    )

    # 데이터베이스 설정 옵션
    setup_group = parser.add_argument_group("데이터베이스 설정")
    setup_group.add_argument(
        "--setup-db", action="store_true", help="새 노션 데이터베이스 생성 및 설정"
    )
    setup_group.add_argument(
        "--parent-page", help="노션 상위 페이지 ID (데이터베이스 생성 위치)"
    )
    setup_group.add_argument(
        "--db-name",
        default="Hugo Blog Posts",
        help="생성할 데이터베이스 이름 (기본값: 'Hugo Blog Posts')",
    )
    setup_group.add_argument(
        "--target-folder", default="posts", help="컨텐츠 대상 폴더 (기본값: 'posts')"
    )

    # 데이터베이스 마이그레이션 옵션
    migrate_group = parser.add_argument_group("데이터베이스 마이그레이션")
    migrate_group.add_argument(
        "--migrate-db",
        action="store_true",
        help="기존 노션 데이터베이스에서 마이그레이션",
    )
    migrate_group.add_argument(
        "--source-db", help="소스 데이터베이스 ID (마이그레이션 시 필요)"
    )

    # 증분 처리 옵션
    incremental_group = parser.add_argument_group("증분 처리 옵션")
    incremental_group.add_argument(
        "--incremental",
        action="store_true",
        help="변경된 페이지만 처리 (기본값)",
        default=True,
    )
    incremental_group.add_argument(
        "--full-sync", action="store_true", help="모든 페이지 강제 재처리"
    )
    incremental_group.add_argument(
        "--state-file",
        default=".notion-hugo-state.json",
        help="메타데이터 파일 위치 (기본값: .notion-hugo-state.json)",
    )
    incremental_group.add_argument(
        "--dry-run", action="store_true", help="실제 변환 없이 변경사항만 확인"
    )

    # 대화형 모드 옵션
    interactive_group = parser.add_argument_group("대화형 모드")
    interactive_group.add_argument(
        "--interactive", "-i", action="store_true", help="대화형 설정 모드로 실행"
    )

    return parser.parse_args()


def run_notion_pipeline(
    incremental: bool = True,
    state_file: str = ".notion-hugo-state.json",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Notion 파이프라인을 실행합니다 (마크다운 변환).

    Args:
        incremental: 증분 처리 여부 (기본값: True)
        state_file: 메타데이터 파일 경로 (기본값: ".notion-hugo-state.json")
        dry_run: 실제 변환 없이 변경사항만 확인 (기본값: False)

    Returns:
        처리 결과 (성공 여부, 페이지 ID 목록, 결과 목록)
    """
    try:
        # 환경 변수 로드
        load_dotenv()

        if not os.environ.get("NOTION_TOKEN"):
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다")

        # 설정 로드
        config = load_config()
        print("[Info] 설정 로드 완료")

        # 메타데이터 관리자 초기화
        metadata = MetadataManager(state_file) if incremental else None
        if incremental:
            print(f"[Info] 메타데이터 로드 완료 (파일: {state_file})")

        # 증분 처리 모드 표시
        if incremental:
            print("[Info] 증분 처리 모드: 변경된 페이지만 처리합니다")
        else:
            print("[Info] 전체 동기화 모드: 모든 페이지를 처리합니다")

        if dry_run:
            print("[Info] 테스트 모드: 실제 변환 없이 변경사항만 확인합니다")

        # Notion 클라이언트 생성
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))

        # Hugo 구조 확인
        processor = HugoProcessor()
        processor.ensure_structure()

        # 데이터베이스와 페이지 처리 (증분 처리 적용)
        if incremental and metadata:
            db_results = process_databases_incremental(
                notion, config, metadata, dry_run
            )
            page_results = process_pages_incremental(notion, config, metadata, dry_run)
        else:
            db_results = process_databases(notion, config)
            page_results = process_pages(notion, config)

        # 모든 페이지 ID와 결과 결합
        all_page_ids = db_results["page_ids"] + page_results["page_ids"]
        all_results = db_results["results"] + page_results["results"]

        if not dry_run:
            # 고아 파일 정리 (메타데이터 기반)
            if incremental and metadata:
                cleanup_orphaned_files_with_metadata(all_page_ids, metadata)
            else:
                cleanup_orphaned_files(all_page_ids)

            # 메타데이터 저장
            if incremental and metadata:
                metadata.save()
                print(f"[Info] 메타데이터 저장 완료 (파일: {state_file})")

        # 요약 출력
        print_results(all_results)

        # 변환 실패 여부 확인
        has_errors = any(len(result["errors"]) > 0 for result in all_results)

        return {
            "success": not has_errors,
            "page_ids": all_page_ids,
            "results": all_results,
        }

    except Exception as e:
        print(f"[Error] {str(e)}")
        # Critical: Exit with error code when API fails
        sys.exit(1)


def process_databases_incremental(
    notion: Client,
    config: Config,
    metadata: MetadataManager,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    설정된 Notion 데이터베이스의 페이지를 증분 처리합니다.

    Args:
        notion: Notion API 클라이언트
        config: 앱 설정
        metadata: 메타데이터 관리자
        dry_run: 실제 변환 없이 변경사항만 확인

    Returns:
        처리된 페이지 ID 목록과 처리 결과를 포함하는 딕셔너리
    """
    page_ids = []
    results = []

    print("[Info] 마운트된 데이터베이스 증분 처리 시작")

    for mount in config["mount"]["databases"]:
        ensure_directory(f"content/{mount['target_folder']}")
        all_pages = []

        # 데이터베이스의 모든 페이지 메타데이터 조회
        for page_result in iterate_paginated_api(
            notion.databases.query, {"database_id": mount["database_id"]}
        ):
            page = cast(Dict[str, Any], page_result)
            if page.get("object") != "page":
                continue

            all_pages.append(page)
            page_ids.append(page["id"])

        # 변경된 페이지만 필터링
        changed_pages = metadata.get_changed_pages(all_pages)

        if changed_pages:
            if dry_run:
                print(
                    f"[Info] 데이터베이스 {mount['database_id']}에서 변경된 페이지 {len(changed_pages)}/{len(all_pages)}개 (테스트 모드)"
                )
                # 건너뛴 페이지 ID만 메타데이터에 추가
                for page in changed_pages:
                    metadata.update_page_status(
                        page["id"],
                        status="skipped",
                        last_edited=page.get("last_edited_time"),
                    )
                results.append(
                    {
                        "totalProcessed": len(changed_pages),
                        "success": [],
                        "errors": [],
                        "skipped": [
                            {"pageId": p["id"], "reason": "Dry run"}
                            for p in changed_pages
                        ],
                    }
                )
            else:
                print(
                    f"[Info] 데이터베이스 {mount['database_id']}에서 변경된 페이지 {len(changed_pages)}/{len(all_pages)}개 처리 중"
                )
                result = batch_process_pages_with_metadata(
                    changed_pages, notion, mount, metadata, config
                )
                results.append(result)
        else:
            print(
                f"[Info] 데이터베이스 {mount['database_id']}에서 변경된 페이지 없음 ({len(all_pages)}개 페이지 검사됨)"
            )
            # 빈 결과 추가
            results.append(
                {"totalProcessed": 0, "success": [], "errors": [], "skipped": []}
            )

    return {"page_ids": page_ids, "results": results}


def process_pages_incremental(
    notion: Client,
    config: Config,
    metadata: MetadataManager,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    설정된 Notion 페이지를 증분 처리합니다.

    Args:
        notion: Notion API 클라이언트
        config: 앱 설정
        metadata: 메타데이터 관리자
        dry_run: 실제 변환 없이 변경사항만 확인

    Returns:
        처리된 페이지 ID 목록과 처리 결과를 포함하는 딕셔너리
    """
    page_ids = []
    results = []

    if "pages" not in config["mount"]:
        return {"page_ids": [], "results": []}

    print("[Info] 마운트된 페이지 증분 처리 시작")

    for mount in config["mount"]["pages"]:
        page_result = notion.pages.retrieve(page_id=mount["page_id"])
        page = cast(Dict[str, Any], page_result)

        if not is_full_page(page):
            continue

        page_ids.append(page["id"])

        # 변경 확인
        if page["id"] in metadata.get_processed_page_ids():
            last_edited = page.get("last_edited_time")
            stored_edited = metadata.metadata["pages"][page["id"]].get("last_edited")

            if last_edited == stored_edited:
                print(f"[Info] 페이지 {page['id']} 변경 없음, 건너뜁니다")
                # 빈 결과 추가
                results.append(
                    {"totalProcessed": 0, "success": [], "errors": [], "skipped": []}
                )
                continue

        if dry_run:
            print(f"[Info] 페이지 {page['id']} 변경 감지됨 (테스트 모드)")
            metadata.update_page_status(
                page["id"], status="skipped", last_edited=page.get("last_edited_time")
            )
            results.append(
                {
                    "totalProcessed": 1,
                    "success": [],
                    "errors": [],
                    "skipped": [{"pageId": page["id"], "reason": "Dry run"}],
                }
            )
        else:
            result = batch_process_pages_with_metadata(
                [page], notion, mount, metadata, config
            )
            results.append(result)

    return {"page_ids": page_ids, "results": results}


def batch_process_pages_with_metadata(
    pages: List[Dict[str, Any]],
    notion: Client,
    mount: Union[DatabaseMount, PageMount],
    metadata: MetadataManager,
    config: Config,
) -> BatchProcessResult:
    """
    페이지 처리 결과를 메타데이터에 저장하면서 여러 페이지를 일괄 처리합니다.

    Args:
        pages: 처리할 페이지 목록
        notion: Notion API 클라이언트
        mount: 마운트 설정
        metadata: 메타데이터 관리자

    Returns:
        BatchProcessResult: 처리 결과
    """
    result = {"totalProcessed": 0, "success": [], "errors": [], "skipped": []}

    target_folder = mount["target_folder"]
    ensure_directory(f"content/{target_folder}")

    for page in pages:
        page_id = page["id"]
        last_edited = None  # UnboundLocalError 방지를 위해 초기화
        try:
            # 마지막 편집 시간 저장
            last_edited = page.get("last_edited_time")

            # 페이지 처리 (수정된 save_page 함수는 target_folder를 받음)
            content = save_page(page, notion, target_folder, config)

            # 성공 정보 추가
            result["success"].append(
                {
                    "pageId": page_id,
                    "title": get_page_title(page),
                    "path": f"content/{target_folder}/{page_id}.md",
                }
            )

            # 메타데이터 업데이트
            if content is not None:
                metadata.update_page_status(
                    page_id,
                    status="success",
                    last_edited=last_edited,
                    target_path=f"content/{target_folder}/{page_id}.md",
                    hash=metadata.compute_content_hash(content),
                )
            else:
                # 콘텐츠 생성 실패 시에도 상태 기록
                metadata.update_page_status(
                    page_id,
                    status="error",
                    last_edited=last_edited,
                    error="Content generation returned None.",
                )

        except Exception as e:
            print(f"[Error] 페이지 {page_id} 처리 실패: {str(e)}")
            # 오류 정보 추가
            result["errors"].append({"pageId": page_id, "error": str(e)})

            # 메타데이터 업데이트 (오류 상태)
            metadata.update_page_status(
                page_id, status="error", last_edited=last_edited, error=str(e)
            )

        result["totalProcessed"] += 1

    return cast(BatchProcessResult, result)


def cleanup_orphaned_files_with_metadata(
    current_page_ids: List[str], metadata: MetadataManager
) -> None:
    """
    더 이상 Notion에 존재하지 않는 파일을 메타데이터와 함께 정리합니다.

    Args:
        current_page_ids: 현재 존재하는 페이지 ID 목록
        metadata: 메타데이터 관리자
    """
    print("[Info] 메타데이터 기반 고아 파일 확인 중")

    # 메타데이터에서 현재 존재하지 않는 페이지 ID 찾기
    orphaned_ids = metadata.get_orphaned_page_ids(current_page_ids)
    removed_count = 0

    if orphaned_ids:
        print(f"[Info] {len(orphaned_ids)}개의 고아 페이지 ID 발견")

        for orphaned_id in orphaned_ids:
            # 메타데이터에서 대상 경로 확인
            target_path = metadata.metadata["pages"][orphaned_id].get("target_path")

            if target_path and os.path.exists(target_path):
                print(f"[Info] 고아 파일 제거 중: {target_path}")
                os.remove(target_path)
                removed_count += 1

            # 메타데이터에서 제거
            metadata.remove_page(orphaned_id)

    if removed_count > 0:
        print(f"[Info] {removed_count}개의 고아 파일을 제거했습니다")
    else:
        print("[Info] 고아 파일이 없습니다")


def get_page_title(page: Dict[str, Any]) -> str:
    """
    페이지 제목 추출

    Args:
        page: 페이지 객체

    Returns:
        페이지 제목
    """
    if (
        "properties" in page
        and "Name" in page["properties"]
        and page["properties"]["Name"].get("type") == "title"
    ):
        title_objects = page["properties"]["Name"].get("title", [])
        if title_objects:
            return "".join(
                title_obj.get("plain_text", "") for title_obj in title_objects
            )
    return "Untitled"


def run_hugo_pipeline(
    hugo_args: Optional[List[str]] = None, build: bool = True
) -> Dict[str, Any]:
    """
    Hugo 파이프라인을 실행합니다 (전처리 및 빌드).

    Args:
        hugo_args: Hugo 명령줄 인수
        build: 빌드 여부

    Returns:
        처리 결과 (전처리 성공 여부, 빌드 성공 여부)
    """
    if hugo_args is None:
        hugo_args = []

    processor = HugoProcessor()

    # 전처리 실행
    preprocess_result = processor.preprocess(hugo_args)

    # 빌드 실행 (선택적)
    build_result = None
    if build and preprocess_result == 0:
        build_result = processor.build(hugo_args)

    return {
        "preprocess_success": preprocess_result == 0,
        "build_success": build_result == 0 if build_result is not None else None,
    }


def process_databases(notion: Client, config: Config) -> Dict[str, Any]:
    """
    설정된 Notion 데이터베이스의 페이지를 처리합니다.

    Args:
        notion: Notion API 클라이언트
        config: 앱 설정

    Returns:
        처리된 페이지 ID 목록과 처리 결과를 포함하는 딕셔너리
    """
    page_ids = []
    results = []

    print("[Info] 마운트된 데이터베이스 처리 시작")

    for mount in config["mount"]["databases"]:
        ensure_directory(f"content/{mount['target_folder']}")
        pages = []

        # 데이터베이스의 모든 페이지 조회
        for page_result in iterate_paginated_api(
            notion.databases.query, {"database_id": mount["database_id"]}
        ):
            page = cast(Dict[str, Any], page_result)
            if page.get("object") != "page":
                continue

            pages.append(page)
            page_ids.append(page["id"])

        if pages:
            print(
                f"[Info] 데이터베이스 {mount['database_id']}에서 {len(pages)}개 페이지 처리 중"
            )
            result = batch_process_pages(pages, notion, mount, config)
            results.append(result)

    return {"page_ids": page_ids, "results": results}


def process_pages(notion: Client, config: Config) -> Dict[str, Any]:
    """
    설정된 Notion 페이지를 처리합니다.

    Args:
        notion: Notion API 클라이언트
        config: 앱 설정

    Returns:
        처리된 페이지 ID 목록과 처리 결과를 포함하는 딕셔너리
    """
    page_ids = []
    results = []

    print("[Info] 마운트된 페이지 처리 시작")

    for mount in config["mount"]["pages"]:
        page_result = notion.pages.retrieve(page_id=mount["page_id"])
        page = cast(Dict[str, Any], page_result)

        if not is_full_page(page):
            continue

        page_ids.append(page["id"])
        result = batch_process_pages([page], notion, mount, config)
        results.append(result)

    return {"page_ids": page_ids, "results": results}


def cleanup_orphaned_files(page_ids: List[str]) -> None:
    """
    더 이상 Notion에 존재하지 않는 파일을 정리합니다.

    Args:
        page_ids: 현재 처리된 페이지 ID 목록
    """
    print("[Info] 고아 파일 확인 중")
    print(f"[Debug] 현재 페이지 ID: {', '.join(page_ids)}")

    content_files = get_all_content_files("content")
    removed_count = 0

    for file in content_files:
        file_id = file["metadata"].get("id")
        print(f"[Debug] 파일 확인 중: {file['filepath']} (ID: {file_id})")

        # 아직 처리 중인 파일은 건너뜀
        if file_id in page_ids:
            print(f"[Debug] 파일 {file['filepath']}은 아직 활성 상태입니다")
            continue

        # 적절한 메타데이터가 없는 파일은 건너뜀
        if not file_id:
            print(
                f"[Warn] 파일 {file['filepath']}에 유효한 ID가 없어 정리를 건너뜁니다"
            )
            continue

        print(f"[Info] 고아 파일 제거 중: {file['filepath']}")
        os.remove(file["filepath"])
        removed_count += 1

    if removed_count > 0:
        print(f"[Info] {removed_count}개의 고아 파일을 제거했습니다")
    else:
        print("[Info] 고아 파일이 없습니다")


def validate_hugo_build() -> bool:
    """
    Hugo 빌드 결과를 검증합니다.
    
    Returns:
        빌드가 유효한지 여부
    """
    public_dir = "public"
    
    # public 디렉토리 존재 확인
    if not os.path.exists(public_dir):
        print(f"[Error] {public_dir} 디렉토리가 존재하지 않습니다")
        return False
    
    # public 디렉토리가 비어있는지 확인
    if not os.listdir(public_dir):
        print(f"[Error] {public_dir} 디렉토리가 비어있습니다")
        return False
    
    # index.html 파일 존재 확인
    index_file = os.path.join(public_dir, "index.html")
    if not os.path.exists(index_file):
        print(f"[Error] {index_file} 파일이 없습니다")
        return False
    
    # index.html 파일 크기 확인 (너무 작으면 빈 페이지)
    try:
        file_size = os.path.getsize(index_file)
        if file_size < 100:  # 100바이트 미만이면 빈 페이지로 간주
            print(f"[Error] {index_file} 파일이 너무 작습니다 ({file_size} bytes)")
            return False
    except OSError as e:
        print(f"[Error] {index_file} 파일 크기 확인 실패: {e}")
        return False
    
    # 기본 콘텐츠 폴더 확인
    posts_dir = os.path.join(public_dir, "posts")
    if os.path.exists(posts_dir):
        post_files = [f for f in os.listdir(posts_dir) if f.endswith('.html')]
        print(f"[Info] {len(post_files)}개의 포스트 페이지가 생성되었습니다")
    
    print("[Info] Hugo 빌드 검증 통과")
    return True


def print_results(results: List[BatchProcessResult]) -> None:
    """
    처리 결과를 출력합니다.

    Args:
        results: 처리 결과 목록
    """
    totals = {"processed": 0, "success": 0, "errors": 0, "skipped": 0}

    for result in results:
        totals["processed"] += result["totalProcessed"]
        totals["success"] += len(result["success"])
        totals["errors"] += len(result["errors"])
        totals["skipped"] += len(result["skipped"])

    print("\n=== 변환 요약 ===")
    print(f"총 처리: {totals['processed']}")
    print(f"성공: {totals['success']}")
    print(f"건너뜀: {totals['skipped']}")
    print(f"오류: {totals['errors']}")

    if totals["errors"] > 0:
        print("\n발생한 오류:")
        for result in results:
            for error in result["errors"]:
                print(f"- 페이지 {error['pageId']}: {error['error']}")


def handle_signal(sig, frame):
    """
    인터럽트 시그널 처리 핸들러
    """
    print("\n인터럽트 시그널을 받았습니다. 종료합니다.")
    sys.exit(130)  # 130은 SIGINT에 의한 종료를 나타내는 표준 종료 코드


def run_setup_database(
    parent_page_id: Optional[str], database_name: str, target_folder: str
) -> Dict[str, Any]:
    """
    새 노션 데이터베이스를 설정합니다.

    Args:
        parent_page_id: 부모 페이지 ID (옵션). 지정하지 않으면 워크스페이스 루트에 생성
        database_name: 데이터베이스 이름
        target_folder: 대상 폴더

    Returns:
        처리 결과
    """
    try:
        # 환경 변수 로드
        load_dotenv()

        from .cli_utils import (
            print_header,
            print_step,
            print_success,
            print_error,
            print_info,
            print_id_info,
        )

        if not os.environ.get("NOTION_TOKEN"):
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다")

        print_header("노션 데이터베이스 설정")

        # 생성 위치 표시
        location = (
            f"상위 페이지 '{parent_page_id}'" if parent_page_id else "워크스페이스 루트"
        )
        print_info(f"{location}에 '{database_name}' 데이터베이스를 생성합니다.")

        # NotionSetup 인스턴스 생성
        setup_config: NotionSetupConfig = {
            "parent_page_id": parent_page_id,
            "database_name": database_name,
            "notion_token": os.environ.get("NOTION_TOKEN"),
        }
        setup = NotionSetup(setup_config)

        # 데이터베이스 생성
        try:
            print_step("1", "데이터베이스 생성")
            database = setup.create_hugo_database()
        except ValueError as e:
            if (
                "워크스페이스 루트에 데이터베이스를 생성할 권한이 없습니다" in str(e)
                and not parent_page_id
            ):
                print_error(
                    "워크스페이스 루트에 데이터베이스를 생성할 권한이 없습니다."
                )
                print_info(
                    "1. Notion 통합(integration) 설정에서 '워크스페이스 콘텐츠 생성' 기능을 활성화하거나"
                )
                print_info(
                    "2. 대화형 모드를 사용하여 특정 페이지 아래에 데이터베이스를 생성하세요."
                )
                return {"success": False, "error": str(e)}
            raise

        # 샘플 포스트 생성
        print_step("2", "샘플 포스트 생성")
        post = setup.create_sample_post(database["id"])

        # 설정 파일 업데이트
        print_step("3", "설정 파일 업데이트")
        print_info(f"대상 폴더: {target_folder}")
        setup.update_config(database["id"], target_folder)

        print_header("데이터베이스 설정 완료")

        # ID 정보 명확하게 표시
        print_id_info(
            "데이터베이스",
            database["id"],
            f"https://notion.so/{database['id'].replace('-', '')}",
        )
        print_id_info(
            "샘플 페이지",
            post["id"],
            f"https://notion.so/{post['id'].replace('-', '')}",
        )

        print_step("다음 단계", "노션-휴고 동기화 실행")
        print_info("python notion_hugo_app.py 명령으로 동기화를 시작하세요")

        return {"success": True, "database_id": database["id"]}

    except Exception as e:
        print(f"[Error] 데이터베이스 설정 실패: {str(e)}")
        return {"success": False, "error": str(e)}


def run_migrate_database(
    source_db_id: str, parent_page_id: Optional[str], target_folder: str
) -> Dict[str, Any]:
    """
    기존 노션 데이터베이스에서 마이그레이션합니다.

    Args:
        source_db_id: 소스 데이터베이스 ID
        parent_page_id: 부모 페이지 ID (옵션). 지정하지 않으면 워크스페이스 루트에 생성
        target_folder: 대상 폴더

    Returns:
        처리 결과
    """
    try:
        # 환경 변수 로드
        load_dotenv()

        from .cli_utils import (
            print_header,
            print_step,
            print_success,
            print_error,
            print_info,
            print_id_info,
        )

        if not os.environ.get("NOTION_TOKEN"):
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다")

        print_header("노션 데이터베이스 마이그레이션")

        # 생성 위치 표시
        location = (
            f"상위 페이지 '{parent_page_id}'" if parent_page_id else "워크스페이스 루트"
        )
        print_info(f"소스 데이터베이스 ID: {source_db_id}")
        print_info(f"대상 위치: {location}")

        # NotionMigration 인스턴스 생성
        migration_config: NotionSetupConfig = {
            "parent_page_id": parent_page_id,
            "database_name": "Migrated Hugo Blog Posts",
            "notion_token": os.environ.get("NOTION_TOKEN"),
        }
        migration = NotionMigration(migration_config)

        # 마이그레이션 실행
        print_step("1", "소스 데이터베이스 검증")
        result = migration.migrate_database(source_db_id, target_folder)

        if result["success"]:
            print_header("데이터베이스 마이그레이션 완료")

            # ID 정보 명확하게 표시
            print_id_info(
                "새 데이터베이스",
                result["new_database_id"],
                f"https://notion.so/{result['new_database_id'].replace('-', '')}",
            )

            print_step("다음 단계", "노션-휴고 동기화 실행")
            print_info("python notion_hugo_app.py 명령으로 동기화를 시작하세요")

            return {"success": True, "database_id": result["new_database_id"]}
        else:
            print_error("마이그레이션에 실패했습니다.")
            return {"success": False, "error": result.get("error", "알 수 없는 오류")}

    except Exception as e:
        print(f"[Error] 데이터베이스 마이그레이션 실패: {str(e)}")
        return {"success": False, "error": str(e)}


def run_interactive_setup() -> Dict[str, Any]:
    """
    대화형 모드로 설정을 진행합니다.

    Returns:
        설정 결과
    """
    from .cli_utils import (
        clear_screen,
        print_header,
        print_step,
        print_info,
        print_error,
        print_success,
        print_warning,
        ask_yes_no,
        ask_input,
        show_menu,
        is_notion_page_id,
        is_notion_database_id,
        extract_notion_id_from_url,
        format_notion_id,
        print_id_info,
    )

    try:
        # 환경 변수 로드
        load_dotenv()

        clear_screen()
        print_header("노션-휴고 통합 설정 마법사")

        # 노션 API 키 확인
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            print_step("1", "노션 API 키 설정")
            print_info("노션 API 키가 설정되어 있지 않습니다.")
            print_info("노션 API 키는 .env 파일에 설정해야 합니다.")
            print_info("방법: https://developers.notion.com/docs/getting-started")
            print_info("1. www.notion.so/my-integrations 방문")
            print_info("2. 새 통합 생성 및 토큰 복사")
            print_info("3. '.env' 파일에 NOTION_TOKEN=your_token 형식으로 추가")

            if ask_yes_no("지금 API 키를 입력하시겠습니까?"):
                api_key = ask_input("노션 API 키를 입력하세요")

                # .env 파일 생성 또는 업데이트
                with open(".env", "w") as f:
                    f.write(f"NOTION_TOKEN={api_key}\n")

                print_success(".env 파일에 API 키가 설정되었습니다.")
                notion_token = api_key
            else:
                print_error("노션 API 키가 필요합니다. 나중에 다시 설정하세요.")
                return {"success": False, "error": "API 키 누락"}

        # 설정 방식 선택
        print_step("2", "설정 방식 선택")
        setup_type = show_menu(
            "사용할 설정 방식을 선택하세요",
            [
                "새 노션 데이터베이스 생성 (처음 사용자)",
                "기존 노션 데이터베이스 마이그레이션 (이미 데이터가 있는 경우)",
            ],
        )

        # 기본 설정
        target_folder = "posts"

        # 타겟 폴더 설정
        print_step("3", "콘텐츠 폴더 설정")
        print_info("콘텐츠가 저장될 Hugo 폴더 경로를 설정합니다.")
        target_folder = ask_input("타겟 폴더명을 입력하세요", "posts")

        if setup_type == 0:  # 새 데이터베이스 생성
            print_step("4", "데이터베이스 생성 위치")
            location_type = show_menu(
                "데이터베이스를 생성할 위치를 선택하세요",
                ["워크스페이스 루트 (권장)", "특정 페이지 아래 (페이지 ID 필요)"],
            )

            parent_page_id = None
            if location_type == 1:  # 특정 페이지 아래
                while True:
                    parent_input = ask_input("상위 페이지 ID 또는 URL을 입력하세요")

                    # URL에서 ID 추출 시도
                    if "notion.so" in parent_input:
                        extracted_id = extract_notion_id_from_url(parent_input)
                        if extracted_id:
                            parent_page_id = extracted_id
                            print_success(
                                f"페이지 ID가 URL에서 추출되었습니다: {format_notion_id(parent_page_id)}"
                            )
                            break

                    # 직접 ID 입력 검증
                    elif is_notion_page_id(parent_input):
                        parent_page_id = parent_input
                        print_success(
                            f"유효한 페이지 ID 형식입니다: {format_notion_id(parent_page_id)}"
                        )
                        break

                    print_warning(
                        "유효한 노션 페이지 ID나 URL이 아닙니다. 다시 시도하세요."
                    )

            # 데이터베이스 이름 설정
            print_step("5", "데이터베이스 이름 설정")
            db_name = ask_input("데이터베이스 이름을 입력하세요", "Hugo Blog Posts")

            # 데이터베이스 설정 실행
            print_step("6", "데이터베이스 생성")
            return run_setup_database(parent_page_id, db_name, target_folder)

        else:  # 기존 데이터베이스 마이그레이션
            print_step("4", "소스 데이터베이스 지정")

            while True:
                source_input = ask_input("소스 데이터베이스 ID 또는 URL을 입력하세요")

                # URL에서 ID 추출 시도
                if "notion.so" in source_input:
                    extracted_id = extract_notion_id_from_url(source_input)
                    if extracted_id:
                        source_db_id = extracted_id
                        print_success(
                            f"데이터베이스 ID가 URL에서 추출되었습니다: {format_notion_id(source_db_id)}"
                        )
                        break

                # 직접 ID 입력 검증
                elif is_notion_database_id(source_input):
                    source_db_id = source_input
                    print_success(
                        f"유효한 데이터베이스 ID 형식입니다: {format_notion_id(source_db_id)}"
                    )
                    break

                print_warning(
                    "유효한 노션 데이터베이스 ID나 URL이 아닙니다. 다시 시도하세요."
                )

            # 대상 위치 설정
            print_step("5", "대상 위치 선택")
            location_type = show_menu(
                "마이그레이션 대상 위치를 선택하세요",
                ["워크스페이스 루트 (권장)", "특정 페이지 아래 (페이지 ID 필요)"],
            )

            parent_page_id = None
            if location_type == 1:  # 특정 페이지 아래
                while True:
                    parent_input = ask_input(
                        "대상 상위 페이지 ID 또는 URL을 입력하세요"
                    )

                    # URL에서 ID 추출 시도
                    if "notion.so" in parent_input:
                        extracted_id = extract_notion_id_from_url(parent_input)
                        if extracted_id:
                            parent_page_id = extracted_id
                            print_success(
                                f"페이지 ID가 URL에서 추출되었습니다: {format_notion_id(parent_page_id)}"
                            )
                            break

                    # 직접 ID 입력 검증
                    elif is_notion_page_id(parent_input):
                        parent_page_id = parent_input
                        print_success(
                            f"유효한 페이지 ID 형식입니다: {format_notion_id(parent_page_id)}"
                        )
                        break

                    print_warning(
                        "유효한 노션 페이지 ID나 URL이 아닙니다. 다시 시도하세요."
                    )

            # 데이터베이스 마이그레이션 실행
            print_step("6", "데이터베이스 마이그레이션")
            return run_migrate_database(source_db_id, parent_page_id, target_folder)

    except Exception as e:
        print(f"[Error] 대화형 설정 실패: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """
    메인 함수 - 통합 파이프라인 실행
    """
    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, handle_signal)

    # 명령줄 인수 파싱
    args = parse_arguments()

    # Hugo 인자 파싱
    hugo_args = args.hugo_args.split() if args.hugo_args else []

    try:
        # 대화형 설정 모드
        if args.interactive:
            interactive_result = run_interactive_setup()

            if not interactive_result["success"]:
                sys.exit(1)

            # 대화형 설정 후 실행 여부 확인
            from .cli_utils import ask_yes_no, print_info

            if ask_yes_no("지금 바로 노션-휴고 동기화를 실행하시겠습니까?"):
                print_info("노션-휴고 동기화를 시작합니다...")
            else:
                print_info(
                    "설정이 완료되었습니다. 나중에 'python notion_hugo_app.py' 명령으로 동기화를 실행하세요."
                )
                return

        # 데이터베이스 설정 모드
        elif args.setup_db:
            # parent_page는 옵션으로 변경
            setup_result = run_setup_database(
                args.parent_page,  # None이 될 수 있음 (워크스페이스 루트에 생성)
                args.db_name,
                args.target_folder,
            )

            if not setup_result["success"]:
                sys.exit(1)

            # 설정 후 일반 파이프라인 실행 건너뜀
            return

        # 데이터베이스 마이그레이션 모드
        elif args.migrate_db:
            if not args.source_db:
                raise ValueError("--source-db 인자가 필요합니다 (소스 데이터베이스 ID)")

            # parent_page는 옵션으로 변경
            migrate_result = run_migrate_database(
                args.source_db,
                args.parent_page,  # None이 될 수 있음 (워크스페이스 루트에 생성)
                args.target_folder,
            )

            if not migrate_result["success"]:
                sys.exit(1)

            # 마이그레이션 후 일반 파이프라인 실행 건너뜀
            return

        # 일반 파이프라인 모드
        if not args.hugo_only:
            # 증분 처리 설정
            incremental = args.incremental and not args.full_sync

            # Notion 파이프라인 실행 (증분 처리 옵션 적용)
            print("=== Notion 파이프라인 실행 중... ===")
            notion_result = run_notion_pipeline(
                incremental=incremental,
                state_file=args.state_file,
                dry_run=args.dry_run,
            )
            print(f"Notion 처리 완료: {notion_result['success']}")
            
            # Critical: Check if Notion pipeline failed
            if not notion_result.get('success', False):
                print("[Error] Notion 파이프라인 실패 - 배포 중단")
                sys.exit(1)

            # 테스트 모드일 경우 Hugo 빌드 건너뛰기
            if args.dry_run:
                print("[Info] 테스트 모드: Hugo 빌드 건너뜀")
                return

        if not args.notion_only:
            # Hugo 파이프라인 실행
            print("=== Hugo 파이프라인 실행 중... ===")
            hugo_result = run_hugo_pipeline(hugo_args, not args.no_build)

            if hugo_result["preprocess_success"]:
                print("Hugo 전처리 완료")
            else:
                print("Hugo 전처리 중 오류 발생")

            if hugo_result["build_success"] is not None:
                if hugo_result["build_success"]:
                    print("Hugo 빌드 완료")
                    
                    # Critical: Validate build output
                    if not validate_hugo_build():
                        print("[Error] Hugo 빌드 검증 실패 - 빈 콘텐츠 감지")
                        sys.exit(1)
                        
                else:
                    print("Hugo 빌드 중 오류 발생")
                    sys.exit(1)

        print("=== 모든 작업이 완료되었습니다 ===")

    except Exception as e:
        print(f"[Error] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
