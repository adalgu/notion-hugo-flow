"""
파일 및 파일명 관련 유틸리티 함수

이 모듈은 파일 처리 및 파일명 생성에 관련된 유틸리티 함수를 제공합니다.
"""

import os
import re
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional

from ..config_enhanced import FilenameConfig


def ensure_directory(path: str) -> None:
    """
    디렉토리가 존재하지 않는 경우 생성합니다.

    Args:
        path: 생성할 디렉토리 경로
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def sanitize_filename(title: str) -> str:
    """
    제목을 파일명으로 사용할 수 있도록 정리합니다.

    Args:
        title: 원본 제목

    Returns:
        정리된 파일명
    """
    # 특수문자 제거 및 공백을 하이픈으로 변환
    filename = re.sub(r"[^\w\s-]", "", title).strip().lower()
    filename = re.sub(r"[\s]+", "-", filename)

    return filename


def generate_filename(
    properties: Dict[str, Any], page_id: str, config: Optional[FilenameConfig]
) -> str:
    """
    설정 기반으로 파일명을 생성합니다.

    Args:
        properties: 페이지 속성
        page_id: 페이지 ID
        config: 파일명 생성 설정

    Returns:
        생성된 파일명
    """
    format_type = config.get("format", "uuid") if config else "uuid"

    # UUID 형식 (기존 방식)
    if format_type == "uuid":
        return page_id

    title = properties.get("title", "untitled")

    # 한글 제목 처리
    korean_title_handling = config.get("korean_title", "slug") if config else "slug"
    if korean_title_handling == "slug":
        title = sanitize_filename(title)
    # 'as-is' 인 경우 그대로 사용

    # title 형식
    if format_type == "title":
        return title

    # date-title 형식
    elif format_type == "date-title":
        date_format = config.get("date_format", "%Y-%m-%d") if config else "%Y-%m-%d"

        # 날짜 추출 (properties에서 date 필드 또는 현재 날짜 사용)
        date_str = properties.get("date")
        if date_str:
            try:
                # ISO 형식 날짜 문자열을 datetime 객체로 변환
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_formatted = date_obj.strftime(date_format)
            except (ValueError, TypeError):
                # 날짜 변환 실패 시 현재 날짜 사용
                date_formatted = datetime.now().strftime(date_format)
        else:
            # date 필드가 없는 경우 현재 날짜 사용
            date_formatted = datetime.now().strftime(date_format)

        return f"{date_formatted}-{title}"

    # 알 수 없는 형식은 기본값(page_id) 반환
    return page_id


def get_filename_with_extension(
    properties: Dict[str, Any],
    page_id: str,
    config: Optional[FilenameConfig],
    extension: str = ".md",
) -> str:
    """
    확장자가 포함된 파일명을 생성합니다.

    Args:
        properties: 페이지 속성
        page_id: 페이지 ID
        config: 파일명 생성 설정
        extension: 파일 확장자 (기본값: .md)

    Returns:
        확장자가 포함된 파일명
    """
    base_filename = generate_filename(properties, page_id, config)
    return f"{base_filename}{extension}"
