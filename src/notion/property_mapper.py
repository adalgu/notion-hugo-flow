#!/usr/bin/env python3
"""
Notion-Hugo Property Mapping System

Manages mappings between Notion database properties and Hugo front matter.
최소한 속성, 추천 속성(콘텐츠 제어, 메타데이터, 분류 등)을 정의하고 처리합니다.
"""

from typing import Dict, List, Any, Optional


# Notion system properties (automatically provided by Notion API)
NOTION_SYSTEM_PROPERTIES = {
    "created_time": {
        "description": "Notion page creation time",
        "fallback_for": "date",  # Date 속성이 없을 때 이 값 사용
    },
    "last_edited_time": {
        "description": "Notion page last modified time",
        "hugo_key": "lastmod",
        "fallback_for": "lastModified",  # lastModified 속성이 없을 때 사용
    },
}

# Minimal properties (essential for blog publishing)
MINIMAL_PROPERTIES = {
    "title": {  # 노션 속성 이름
        "hugo_key": "title",  # Hugo frontmatter 키
        "default": "Untitled",  # 기본값
        "description": "Page title",
    },
    "date": {
        "hugo_key": "date",
        "type": "date",
        "default": "<created_time>",  # 생성 시간을 기본값으로 사용
        "description": "발행일",
    },
    "id": {
        "hugo_key": "notion_id",
        "default": "<page_id>",
        "description": "Notion page ID (for internal use)",
    },
}

# Recommended properties - Content Control
CONTENT_CONTROL_PROPERTIES = {
    "skipRendering": {
        "type": "checkbox",
        "description": "Completely skip this page during Notion to Markdown conversion",
        "default": False,
    },
    "isPublished": {
        "hugo_key": "draft",
        "type": "checkbox",
        "description": "Publication status (true means draft=false, false means draft=true)",
        "default": False,
        "affects": "draft",
        "inverse": True,  # isPublished가 true면 draft는 false
    },
    "expiryDate": {
        "hugo_key": "expiryDate",
        "type": "date",
        "description": "Expiry date (content will be removed from the site after this date)",
    },
}

# Recommended properties - Metadata
METADATA_PROPERTIES = {
    "description": {
        "hugo_key": "description",
        "description": "Page description (for meta tags, critical for SEO)",
    },
    "summary": {
        "hugo_key": "summary",
        "description": "Content summary (used for previews)",
        "fallback": "description",  # description 값 사용
    },
    "lastModified": {
        "hugo_key": "lastmod",
        "type": "date",
        "description": "Last modified date (default: Notion's last_edited_time)",
    },
    "slug": {
        "hugo_key": "slug",
        "description": "URL path (automatically generated from title if not specified)",
    },
    "author": {"hugo_key": "author", "description": "Author"},
    "weight": {
        "hugo_key": "weight",
        "type": "number",
        "description": "Page sorting order (lower values appear first)",
    },
}

# Recommended properties - Taxonomy
TAXONOMY_PROPERTIES = {
    "categories": {
        "hugo_key": "categories",
        "description": "Category classification (primary category)",
    },
    "tags": {"hugo_key": "tags", "description": "List of tags (detailed classification)"},
    "keywords": {
        "hugo_key": "keywords",
        "description": "SEO keywords (for search engines)",
        "fallback": "tags",  # tags 값 사용
    },
}

# Recommended properties - Theme Support
THEME_PROPERTIES = {
    "featured": {
        "hugo_key": "featured",
        "type": "checkbox",
        "description": "Specially featured post (theme support varies)",
    },
    "subtitle": {"hugo_key": "subtitle", "description": "Subtitle (supported by some themes)"},
    "linkTitle": {"hugo_key": "linkTitle", "description": "Short title displayed in links"},
    "layout": {"hugo_key": "layout", "description": "Template layout to use"},
}

# 모든 추천 속성
RECOMMENDED_PROPERTIES = {}
RECOMMENDED_PROPERTIES.update(CONTENT_CONTROL_PROPERTIES)
RECOMMENDED_PROPERTIES.update(METADATA_PROPERTIES)
RECOMMENDED_PROPERTIES.update(TAXONOMY_PROPERTIES)
RECOMMENDED_PROPERTIES.update(THEME_PROPERTIES)


class PropertyMapper:
    """Handles mapping between Notion and Hugo properties"""

    def __init__(self, config=None):
        """
        PropertyMapper 초기화

        Args:
            config: 사용자 정의 매핑 설정 (선택 사항)
        """
        self.config = config or {}
        self.minimal_properties = MINIMAL_PROPERTIES
        self.recommended_properties = RECOMMENDED_PROPERTIES
        self.content_control_properties = CONTENT_CONTROL_PROPERTIES
        self.metadata_properties = METADATA_PROPERTIES
        self.taxonomy_properties = TAXONOMY_PROPERTIES
        self.theme_properties = THEME_PROPERTIES
        self.system_properties = NOTION_SYSTEM_PROPERTIES

    def should_skip_page(self, notion_properties):
        """
        페이지 처리 건너뛰기 여부 결정

        Args:
            notion_properties: 노션 페이지 속성

        Returns:
            건너뛰기 여부 (Boolean)
        """
        # skipRendering 속성을 대소문자 구분 없이 찾기
        skip_rendering_key = None
        for key in notion_properties.keys():
            if key.lower() == "skiprendering":
                skip_rendering_key = key
                break

        # doNotRendering 속성을 대소문자 구분 없이 찾기 (하위 호환성)
        do_not_rendering_key = None
        for key in notion_properties.keys():
            if key.lower() == "donotrendering":
                do_not_rendering_key = key
                break

        # skipRendering 우선, 없으면 doNotRendering 확인
        skip_rendering = False
        if skip_rendering_key:
            skip_rendering = notion_properties.get(skip_rendering_key, False)
        elif do_not_rendering_key:
            skip_rendering = notion_properties.get(do_not_rendering_key, False)

        return skip_rendering == True

    def map_date_properties(self, notion_properties, page):
        """
        날짜 관련 속성 매핑 처리

        Args:
            notion_properties: 노션 페이지 속성
            page: 전체 노션 페이지 객체 (시스템 속성 접근용)

        Returns:
            매핑된 날짜 속성 딕셔너리
        """
        mapped_properties = {}

        # 1. lastmod 처리 (사용자 정의 lastModified 또는 system 속성)
        if "lastModified" in notion_properties and notion_properties["lastModified"]:
            mapped_properties["lastmod"] = notion_properties["lastModified"]
        else:
            mapped_properties["lastmod"] = page.get("last_edited_time")

        # 2. date 처리 (발행일)
        if "date" in notion_properties and notion_properties["date"]:
            # 노션 사용자 정의 Date 속성이 있으면 사용
            mapped_properties["date"] = notion_properties["date"]
        else:
            # 없으면 created_time을 대체값으로 사용
            mapped_properties["date"] = page.get("created_time")

        # 3. expiryDate 처리 (있는 경우만)
        if "expiryDate" in notion_properties and notion_properties["expiryDate"]:
            mapped_properties["expiryDate"] = notion_properties["expiryDate"]

        return mapped_properties

    def process_publication_status(self, notion_properties):
        """
        출판 상태 처리

        Args:
            notion_properties: 노션 페이지 속성

        Returns:
            처리된 출판 상태 속성 딕셔너리
        """
        result = {}

        # isPublished 속성이 있으면 draft 속성 결정 (역의 관계)
        # 대소문자 구분 없이 찾기
        is_published_key = None
        for key in notion_properties.keys():
            if key.lower() == "ispublished":
                is_published_key = key
                break

        if is_published_key and notion_properties[is_published_key] is not None:
            is_published = notion_properties[is_published_key]
            # isPublished=true → draft=false, isPublished=false → draft=true
            result["draft"] = not is_published
        else:
            # 기본값: draft = true (초안 상태)
            result["draft"] = True

        return result

    def process_metadata_properties(self, notion_properties):
        """
        메타데이터 속성 처리 (fallback 적용)

        Args:
            notion_properties: 노션 페이지 속성

        Returns:
            처리된 메타데이터 속성 딕셔너리
        """
        result = {}

        # 1. summary 속성 (fallback: description)
        if "summary" in notion_properties and notion_properties["summary"]:
            result["summary"] = notion_properties["summary"]
        elif "description" in notion_properties and notion_properties["description"]:
            result["summary"] = notion_properties["description"]

        # 2. keywords 속성 (fallback: tags)
        if "keywords" in notion_properties and notion_properties["keywords"]:
            result["keywords"] = notion_properties["keywords"]
        elif "tags" in notion_properties and notion_properties["tags"]:
            result["keywords"] = notion_properties["tags"]

        return result

    def map_properties(self, notion_properties, page):
        """
        노션 속성을 Hugo 속성으로 변환

        Args:
            notion_properties: 노션 페이지 속성
            page: 전체 노션 페이지 객체 (시스템 속성 접근용)

        Returns:
            Hugo frontmatter용 속성 맵
        """
        hugo_properties = {}

        # skipRendering 체크 (여기서 한 번 더 확인)
        if self.should_skip_page(notion_properties):
            return {}  # 빈 속성 반환하여 처리 중단

        # 1. 날짜 속성 매핑 (date, lastmod, expiryDate 등)
        date_properties = self.map_date_properties(notion_properties, page)
        hugo_properties.update(date_properties)

        # 2. 출판 상태 처리 (draft)
        publication_properties = self.process_publication_status(notion_properties)
        hugo_properties.update(publication_properties)

        # 3. 메타데이터 fallback 처리 (summary, keywords 등)
        metadata_properties = self.process_metadata_properties(notion_properties)
        hugo_properties.update(metadata_properties)

        # 4. 최소한 속성 처리
        for key, config in self.minimal_properties.items():
            if "hugo_key" not in config:
                continue

            hugo_key = config["hugo_key"]
            # 이미 처리된 속성은 건너뛰기
            if hugo_key in hugo_properties:
                continue

            if key not in notion_properties or not notion_properties[key]:
                # 기본값 적용
                if "default" in config:
                    if (
                        isinstance(config["default"], str)
                        and config["default"].startswith("<")
                        and config["default"].endswith(">")
                    ):
                        special_value = config["default"][1:-1]
                        if special_value == "page_id":
                            hugo_properties[hugo_key] = page.get("id")
                        # created_time은 이미 date 속성에서 처리됨
                    else:
                        hugo_properties[hugo_key] = config["default"]
            else:
                hugo_properties[hugo_key] = notion_properties[key]

        # 5. 추천 속성 처리 (있는 경우만)
        for key, config in self.recommended_properties.items():
            if "hugo_key" not in config:
                continue

            hugo_key = config["hugo_key"]
            # 이미 처리된 속성은 건너뛰기
            if hugo_key in hugo_properties:
                continue

            if key in notion_properties and notion_properties[key] is not None:
                if config.get("inverse", False):
                    # 역의 관계 (예: isPublished와 draft)
                    inverted_value = not notion_properties[key]
                    hugo_properties[hugo_key] = inverted_value
                else:
                    hugo_properties[hugo_key] = notion_properties[key]

        return hugo_properties

    def create_hugo_frontmatter(self, notion_properties, page):
        """
        노션 속성에서 Hugo 프론트매터 생성

        Args:
            notion_properties: 노션 페이지 속성
            page: 전체 노션 페이지 객체

        Returns:
            Hugo 프론트매터 딕셔너리
        """
        # 속성 매핑 수행
        hugo_properties = self.map_properties(notion_properties, page)

        # 최소한 필수 속성 확인
        for key, config in self.minimal_properties.items():
            if "hugo_key" not in config:
                continue

            hugo_key = config["hugo_key"]
            if hugo_key not in hugo_properties:
                # id 속성은 페이지 ID로 설정
                if hugo_key == "notion_id":
                    hugo_properties[hugo_key] = page.get("id", "")
                # 기타 필수 속성은 기본값 사용
                elif "default" in config:
                    hugo_properties[hugo_key] = config["default"]

        return hugo_properties
