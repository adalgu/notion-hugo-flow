import os
import re
import yaml
from typing import Dict, List, Any, Optional, TypedDict
from notion_client import Client
from tabulate import tabulate

from .types import BatchProcessResult, BatchProcessError, BatchProcessSkipped
from .helpers import iterate_paginated_api
from .property_mapper import PropertyMapper
from .utils.file_utils import ensure_directory, get_filename_with_extension
from .config import Config, DatabaseMount, PageMount
from typing import Union


def convert_notion_to_markdown(blocks: List[Dict[str, Any]], notion: Client) -> str:
    """
    Notion 블록을 마크다운으로 변환합니다.

    Args:
        blocks: Notion 블록 목록
        notion: Notion API 클라이언트

    Returns:
        변환된 마크다운 문자열
    """
    markdown = ""

    for block in blocks:
        block_type = block.get("type")

        if block_type == "paragraph":
            text = extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
            if text:
                markdown += f"{text}\n\n"
            else:
                markdown += "\n"

        elif block_type == "heading_1":
            text = extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
            markdown += f"# {text}\n\n"

        elif block_type == "heading_2":
            text = extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
            markdown += f"## {text}\n\n"

        elif block_type == "heading_3":
            text = extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
            markdown += f"### {text}\n\n"

        elif block_type == "bulleted_list_item":
            text = extract_rich_text(
                block.get("bulleted_list_item", {}).get("rich_text", [])
            )
            markdown += f"- {text}\n"

        elif block_type == "numbered_list_item":
            text = extract_rich_text(
                block.get("numbered_list_item", {}).get("rich_text", [])
            )
            markdown += f"1. {text}\n"

        elif block_type == "to_do":
            text = extract_rich_text(block.get("to_do", {}).get("rich_text", []))
            checked = block.get("to_do", {}).get("checked", False)
            checkbox = "[x]" if checked else "[ ]"
            markdown += f"{checkbox} {text}\n"

        elif block_type == "toggle":
            text = extract_rich_text(block.get("toggle", {}).get("rich_text", []))
            markdown += f"<details>\n<summary>{text}</summary>\n\n"

            # 토글 내부 블록 처리
            if block.get("has_children", False):
                children = list(
                    iterate_paginated_api(
                        notion.blocks.children.list, {"block_id": block["id"]}
                    )
                )
                inner_markdown = convert_notion_to_markdown(children, notion)
                markdown += f"{inner_markdown}\n"

            markdown += "</details>\n\n"

        elif block_type == "code":
            text = extract_rich_text(block.get("code", {}).get("rich_text", []))
            language = block.get("code", {}).get("language", "")
            markdown += f"```{language}\n{text}\n```\n\n"

        elif block_type == "quote":
            text = extract_rich_text(block.get("quote", {}).get("rich_text", []))
            markdown += f"> {text}\n\n"

        elif block_type == "divider":
            markdown += "---\n\n"

        elif block_type == "image":
            image_block = block.get("image", {})
            caption = extract_rich_text(image_block.get("caption", []))

            if image_block.get("type") == "external":
                url = image_block.get("external", {}).get("url", "")
                markdown += f"![{caption}]({url})\n\n"
            elif image_block.get("type") == "file":
                url = image_block.get("file", {}).get("url", "")
                markdown += f"![{caption}]({url})\n\n"

        elif block_type == "table":
            # 테이블 내부 블록 처리
            if block.get("has_children", False):
                table_rows = list(
                    iterate_paginated_api(
                        notion.blocks.children.list, {"block_id": block["id"]}
                    )
                )
                markdown += render_table(table_rows)

        # 하위 블록 처리
        if block.get("has_children", False) and block_type not in ["toggle", "table"]:
            children = list(
                iterate_paginated_api(
                    notion.blocks.children.list, {"block_id": block["id"]}
                )
            )
            inner_markdown = convert_notion_to_markdown(children, notion)
            markdown += inner_markdown

    return markdown


def extract_rich_text(rich_text: List[Dict[str, Any]]) -> str:
    """
    Notion의 rich_text 배열에서 텍스트를 추출하고 서식을 적용합니다.

    Args:
        rich_text: Notion rich_text 배열

    Returns:
        서식이 적용된 마크다운 텍스트
    """
    result = ""

    for text_item in rich_text:
        content = text_item.get("plain_text", "")
        annotations = text_item.get("annotations", {})

        # 서식 적용
        if annotations.get("bold"):
            content = f"**{content}**"
        if annotations.get("italic"):
            content = f"*{content}*"
        if annotations.get("strikethrough"):
            content = f"~~{content}~~"
        if annotations.get("code"):
            content = f"`{content}`"

        # 링크 처리
        if text_item.get("href"):
            content = f"[{content}]({text_item.get('href')})"

        result += content

    return result


def render_table(table_rows: List[Dict[str, Any]]) -> str:
    """
    Notion 테이블 블록을 마크다운 테이블로 변환합니다.

    Args:
        table_rows: 테이블 행 블록 목록

    Returns:
        마크다운 테이블 문자열
    """
    rows = []

    for row_block in table_rows:
        if row_block.get("type") != "table_row":
            continue

        cells = row_block.get("table_row", {}).get("cells", [])
        row = []

        for cell in cells:
            cell_text = extract_rich_text(cell)
            row.append(cell_text)

        rows.append(row)

    if not rows:
        return ""

    # tabulate 라이브러리를 사용하여 마크다운 테이블 생성
    markdown_table = tabulate(rows, headers="firstrow", tablefmt="pipe")
    return f"{markdown_table}\n\n"


def get_page_properties(page: Dict[str, Any]) -> Dict[str, Any]:
    """
    Notion 페이지의 속성을 추출합니다.

    Args:
        page: Notion 페이지 객체

    Returns:
        페이지 속성 딕셔너리
    """
    properties = {}
    page_properties = page.get("properties", {})

    for key, prop in page_properties.items():
        prop_type = prop.get("type")

        if prop_type == "title":
            title_text = extract_rich_text(prop.get("title", []))
            # Remove markdown/HTML bold from title (for Notion->Hugo)
            import re

            title_text = re.sub(
                r"(\*\*|__|<b>|</b>|<strong>|</strong>)", "", title_text
            )
            properties["title"] = title_text

        elif prop_type == "rich_text":
            text = extract_rich_text(prop.get("rich_text", []))
            properties[key.lower()] = text

        elif prop_type == "date":
            date_obj = prop.get("date", {})
            if date_obj:
                start_date = date_obj.get("start")
                end_date = date_obj.get("end")

                if start_date:
                    properties[key.lower()] = start_date
                    if end_date:
                        properties[f"{key.lower()}_end"] = end_date

        elif prop_type == "select":
            select_obj = prop.get("select", {})
            if select_obj and "name" in select_obj:
                properties[key.lower()] = select_obj["name"]

        elif prop_type == "multi_select":
            multi_select = prop.get("multi_select", [])
            if multi_select:
                properties[key.lower()] = [
                    item.get("name") for item in multi_select if "name" in item
                ]

        elif prop_type == "checkbox":
            properties[key.lower()] = prop.get("checkbox", False)

        elif prop_type == "url":
            properties[key.lower()] = prop.get("url", "")

        elif prop_type == "email":
            properties[key.lower()] = prop.get("email", "")

        elif prop_type == "phone_number":
            properties[key.lower()] = prop.get("phone_number", "")

        elif prop_type == "number":
            properties[key.lower()] = prop.get("number")

    # 기본 메타데이터 추가
    properties["id"] = page.get("id")
    properties["created_time"] = page.get("created_time")
    properties["last_edited_time"] = page.get("last_edited_time")

    return properties


def save_page(
    page: Dict[str, Any],
    notion: Client,
    target_folder: str,
    config: Config,
) -> Optional[str]:
    """
    Notion 페이지를 마크다운 파일로 저장합니다.

    Args:
        page: Notion 페이지 객체
        notion: Notion API 클라이언트
        target_folder: 대상 폴더 이름
        config: 애플리케이션 설정 객체

    Returns:
        저장된 콘텐츠 또는 None (오류 발생 시)
    """
    try:
        if not isinstance(page, dict):
            print(f"[Error] 유효하지 않은 페이지 객체: {type(page)}")
            return ""

        # 페이지 속성 추출
        properties = get_page_properties(page)

        # PropertyMapper 사용하여 필수/선택적 속성 처리
        property_mapper = PropertyMapper()

        # skipRendering 확인 (첫 번째 체크)
        if property_mapper.should_skip_page(properties):
            print(f"[Info] 페이지 {page.get('id')} 건너뜀: skipRendering 설정됨")
            return ""

        # 페이지 ID
        page_id = page.get("id", "unknown")

        # 프론트매터 생성 (여기서 두 번째 skipRendering 체크가 일어남)
        frontmatter = property_mapper.create_hugo_frontmatter(properties, page)

        # 빈 프론트매터는 skipRendering으로 인한 것이므로 건너뜀
        if not frontmatter:
            print(f"[Info] 페이지 {page_id} 건너뜀: PropertyMapper에서 빈 속성 반환")
            return ""

        # 대상 디렉토리 및 파일 경로 설정
        target_dir = f"content/{target_folder}"
        ensure_directory(target_dir)

        # 파일명 생성 (설정에 따라 UUID 또는 다른 형식)
        filename = get_filename_with_extension(
            properties, page_id, config.get("filename", {})
        )
        filepath = f"{target_dir}/{filename}"

        # 페이지 내용 가져오기
        blocks = list(
            iterate_paginated_api(notion.blocks.children.list, {"block_id": page["id"]})
        )

        # 마크다운으로 변환
        markdown_content = convert_notion_to_markdown(blocks, notion)

        # 파일 저장
        frontmatter_yaml = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True
        )
        final_content = f"---\n{frontmatter_yaml}---\n\n{markdown_content}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)

        print(f"[Info] 페이지 저장 완료: {filepath}")
        return final_content

    except Exception as e:
        print(f"[Error] 페이지 저장 중 오류 발생: {str(e)}")
        return ""


def batch_process_pages(
    pages: List[Dict[str, Any]],
    notion: Client,
    mount: Union[DatabaseMount, PageMount],
    config: Config,
) -> BatchProcessResult:
    """
    여러 Notion 페이지를 일괄 처리합니다.

    Args:
        pages: Notion 페이지 객체 목록
        notion: Notion API 클라이언트
        mount: 마운트 설정

    Returns:
        일괄 처리 결과
    """
    result: BatchProcessResult = {
        "totalProcessed": len(pages),
        "success": [],
        "errors": [],
        "skipped": [],
    }

    target_folder = mount.get("target_folder", "posts")
    property_mapper = PropertyMapper()

    for page in pages:
        try:
            # 페이지가 보관 처리되었는지 확인
            if page.get("archived", False):
                result["skipped"].append(
                    {"pageId": page["id"], "reason": "Page is archived"}
                )
                continue

            # 페이지 속성 추출하여 doNotRendering 확인
            properties = get_page_properties(page)
            if property_mapper.should_skip_page(properties):
                result["skipped"].append(
                    {"pageId": page["id"], "reason": "skipRendering is set"}
                )
                print(f"[Info] 페이지 {page.get('id')} 건너뜀: skipRendering 설정됨")
                continue

            # 페이지 저장
            content = save_page(page, notion, target_folder, config)

            if content:
                # 제목 가져오기
                title = properties.get("title", "Untitled")

                # 파일명 생성 (설정에 따라 UUID 또는 다른 형식)
                filename = get_filename_with_extension(
                    properties, page["id"], config.get("filename", {})
                )
                result["success"].append(
                    {
                        "pageId": page["id"],
                        "title": title,
                        "path": f"content/{target_folder}/{filename}",
                    }
                )
            else:
                result["errors"].append(
                    {"pageId": page["id"], "error": "Failed to save page"}
                )

        except Exception as e:
            result["errors"].append({"pageId": page["id"], "error": str(e)})

    return result
