#!/usr/bin/env python3
"""
기존 마크다운 파일들의 title에서 볼드 마크다운(**) 제거 스크립트

이 스크립트는 content/posts 디렉토리의 모든 마크다운 파일을 검사하여
YAML frontmatter의 title 필드에서 볼드 마크다운(**), HTML 태그(<b>, <strong>) 등을 제거합니다.
"""

import os
import re
import yaml
from pathlib import Path


def clean_title(title):
    """
    title에서 볼드 마크다운 및 HTML 태그 제거

    Args:
        title: 원본 title 문자열

    Returns:
        정리된 title 문자열
    """
    if not isinstance(title, str):
        return title

    # 볼드 마크다운 및 HTML 태그 제거
    cleaned = re.sub(r"(\*\*|__|<b>|</b>|<strong>|</strong>)", "", title)

    # 연속된 공백을 하나로 정리
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def process_markdown_file(file_path):
    """
    마크다운 파일의 title을 정리

    Args:
        file_path: 처리할 마크다운 파일 경로

    Returns:
        (변경됨 여부, 원본 title, 정리된 title)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # YAML frontmatter 추출
        if not content.startswith("---"):
            print(f"[Skip] {file_path}: YAML frontmatter가 없습니다")
            return False, None, None

        # frontmatter와 본문 분리
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"[Skip] {file_path}: 올바르지 않은 YAML frontmatter 형식")
            return False, None, None

        frontmatter_text = parts[1]
        body = parts[2]

        # YAML 파싱
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            print(f"[Error] {file_path}: YAML 파싱 오류 - {e}")
            return False, None, None

        if not isinstance(frontmatter, dict):
            print(f"[Skip] {file_path}: frontmatter가 딕셔너리가 아닙니다")
            return False, None, None

        # title 확인 및 정리
        original_title = frontmatter.get("title")
        if not original_title:
            print(f"[Skip] {file_path}: title이 없습니다")
            return False, None, None

        cleaned_title = clean_title(original_title)

        # 변경이 필요한지 확인
        if original_title == cleaned_title:
            return False, original_title, cleaned_title

        # title 업데이트
        frontmatter["title"] = cleaned_title

        # YAML 다시 생성
        new_frontmatter_text = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True
        )
        new_content = f"---\n{new_frontmatter_text}---{body}"

        # 파일 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True, original_title, cleaned_title

    except Exception as e:
        print(f"[Error] {file_path}: 처리 중 오류 발생 - {e}")
        return False, None, None


def main():
    """메인 함수"""
    print("=== Title 볼드 마크다운 제거 스크립트 ===")

    # content/posts 디렉토리 확인
    posts_dir = Path("content/posts")
    if not posts_dir.exists():
        print(f"[Error] {posts_dir} 디렉토리가 존재하지 않습니다")
        return

    # 마크다운 파일 목록 수집
    md_files = list(posts_dir.glob("*.md"))
    if not md_files:
        print(f"[Info] {posts_dir}에 마크다운 파일이 없습니다")
        return

    print(f"[Info] {len(md_files)}개의 마크다운 파일을 검사합니다")

    # 통계
    processed_count = 0
    changed_count = 0

    # 각 파일 처리
    for md_file in md_files:
        print(f"\n[Processing] {md_file.name}")

        changed, original_title, cleaned_title = process_markdown_file(md_file)
        processed_count += 1

        if changed:
            changed_count += 1
            print(f"[Changed] Title 수정됨:")
            print(f"  원본: {original_title}")
            print(f"  수정: {cleaned_title}")
        else:
            if original_title:
                print(f"[No Change] Title: {original_title}")

    # 결과 요약
    print(f"\n=== 처리 완료 ===")
    print(f"총 처리된 파일: {processed_count}")
    print(f"변경된 파일: {changed_count}")
    print(f"변경되지 않은 파일: {processed_count - changed_count}")

    if changed_count > 0:
        print(
            f"\n[Success] {changed_count}개 파일의 title에서 볼드 마크다운이 제거되었습니다"
        )
    else:
        print(f"\n[Info] 변경이 필요한 파일이 없습니다")


if __name__ == "__main__":
    main()
