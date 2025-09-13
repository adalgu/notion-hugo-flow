import os
import sys
from typing import Dict, List, Any, Optional
import json
from notion_client import Client
from dotenv import load_dotenv

from .config import load_config
from .utils.helpers import iterate_paginated_api, is_full_page, ensure_directory
from .render import save_page, batch_process_pages
from .file import get_all_content_files
from .types import BatchProcessResult

def process_databases(notion: Client, config: Dict[str, Any]) -> Dict[str, Any]:
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
    
    for mount in config['mount']['databases']:
        ensure_directory(f"content/{mount['target_folder']}")
        pages = []
        
        # 데이터베이스의 모든 페이지 조회
        for page in iterate_paginated_api(notion.databases.query, {
            "database_id": mount['database_id']
        }):
            if page.get('object') != 'page':
                continue
                
            pages.append(page)
            page_ids.append(page['id'])
        
        if pages:
            print(f"[Info] 데이터베이스 {mount['database_id']}에서 {len(pages)}개 페이지 처리 중")
            result = batch_process_pages(pages, notion, mount)
            results.append(result)
    
    return {"page_ids": page_ids, "results": results}

def process_pages(notion: Client, config: Dict[str, Any]) -> Dict[str, Any]:
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
    
    for mount in config['mount']['pages']:
        page = notion.pages.retrieve(page_id=mount['page_id'])
        
        if not is_full_page(page):
            continue
            
        page_ids.append(page['id'])
        result = batch_process_pages([page], notion, mount)
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
        file_id = file['metadata'].get('id')
        print(f"[Debug] 파일 확인 중: {file['filepath']} (ID: {file_id})")
        
        # 아직 처리 중인 파일은 건너뜀
        if file_id in page_ids:
            print(f"[Debug] 파일 {file['filepath']}은 아직 활성 상태입니다")
            continue
        
        # 적절한 메타데이터가 없는 파일은 건너뜀
        if not file_id:
            print(f"[Warn] 파일 {file['filepath']}에 유효한 ID가 없어 정리를 건너뜁니다")
            continue
        
        print(f"[Info] 고아 파일 제거 중: {file['filepath']}")
        os.remove(file['filepath'])
        removed_count += 1
    
    if removed_count > 0:
        print(f"[Info] {removed_count}개의 고아 파일을 제거했습니다")
    else:
        print("[Info] 고아 파일이 없습니다")

def print_results(results: List[BatchProcessResult]) -> None:
    """
    처리 결과를 출력합니다.
    
    Args:
        results: 처리 결과 목록
    """
    totals = {
        "processed": 0,
        "success": 0,
        "errors": 0,
        "skipped": 0
    }
    
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

def main():
    """
    메인 함수
    """
    try:
        # 환경 변수 로드
        load_dotenv()
        
        if not os.environ.get('NOTION_TOKEN'):
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다")
        
        # 설정 로드
        config = load_config()
        print("[Info] 설정 로드 완료")
        
        # Notion 클라이언트 생성 with API version 2025-09-03
        notion = Client(
            auth=os.environ.get('NOTION_TOKEN'),
            notion_version="2025-09-03"
        )
        
        # 데이터베이스와 페이지 처리
        db_results = process_databases(notion, config)
        page_results = process_pages(notion, config)
        
        # 모든 페이지 ID와 결과 결합
        all_page_ids = db_results["page_ids"] + page_results["page_ids"]
        all_results = db_results["results"] + page_results["results"]
        
        # 고아 파일 정리
        cleanup_orphaned_files(all_page_ids)
        
        # 요약 출력
        print_results(all_results)
        
        # 변환 실패 시 오류 코드로 종료
        has_errors = any(len(result["errors"]) > 0 for result in all_results)
        if has_errors:
            sys.exit(1)
            
    except Exception as e:
        print(f"[Error] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
