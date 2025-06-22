import os
import re
from typing import Dict, List, Any, Optional


def convert_rich_text_to_markdown(rich_text: List[Dict[str, Any]]) -> str:
    """
    Notion의 rich_text 배열을 마크다운 텍스트로 변환합니다.

    Args:
        rich_text: Notion rich_text 배열

    Returns:
        마크다운 텍스트
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


def convert_blocks_to_markdown(blocks: List[Dict[str, Any]]) -> str:
    """
    Notion 블록을 마크다운으로 변환합니다.

    Args:
        blocks: Notion 블록 목록

    Returns:
        마크다운 텍스트
    """
    markdown = ""
    list_type = None

    for block in blocks:
        block_type = block.get("type")

        # 리스트 타입 변경 시 줄바꿈 추가
        if list_type and block_type not in ["bulleted_list_item", "numbered_list_item"]:
            markdown += "\n"
            list_type = None

        if block_type == "paragraph":
            text = convert_rich_text_to_markdown(
                block.get("paragraph", {}).get("rich_text", [])
            )
            if text:
                markdown += f"{text}\n\n"
            else:
                markdown += "\n"

        elif block_type == "heading_1":
            text = convert_rich_text_to_markdown(
                block.get("heading_1", {}).get("rich_text", [])
            )
            markdown += f"# {text}\n\n"

        elif block_type == "heading_2":
            text = convert_rich_text_to_markdown(
                block.get("heading_2", {}).get("rich_text", [])
            )
            markdown += f"## {text}\n\n"

        elif block_type == "heading_3":
            text = convert_rich_text_to_markdown(
                block.get("heading_3", {}).get("rich_text", [])
            )
            markdown += f"### {text}\n\n"

        elif block_type == "bulleted_list_item":
            text = convert_rich_text_to_markdown(
                block.get("bulleted_list_item", {}).get("rich_text", [])
            )
            markdown += f"- {text}\n"
            list_type = "bulleted"

        elif block_type == "numbered_list_item":
            text = convert_rich_text_to_markdown(
                block.get("numbered_list_item", {}).get("rich_text", [])
            )
            markdown += f"1. {text}\n"
            list_type = "numbered"

        elif block_type == "to_do":
            text = convert_rich_text_to_markdown(
                block.get("to_do", {}).get("rich_text", [])
            )
            checked = block.get("to_do", {}).get("checked", False)
            checkbox = "[x]" if checked else "[ ]"
            markdown += f"{checkbox} {text}\n"

        elif block_type == "toggle":
            text = convert_rich_text_to_markdown(
                block.get("toggle", {}).get("rich_text", [])
            )
            markdown += f"<details>\n<summary>{text}</summary>\n\n"

            # 토글 내부 블록 처리
            if "children" in block:
                inner_markdown = convert_blocks_to_markdown(block["children"])
                markdown += f"{inner_markdown}\n"

            markdown += "</details>\n\n"

        elif block_type == "code":
            text = convert_rich_text_to_markdown(
                block.get("code", {}).get("rich_text", [])
            )
            language = block.get("code", {}).get("language", "")
            markdown += f"```{language}\n{text}\n```\n\n"

        elif block_type == "quote":
            text = convert_rich_text_to_markdown(
                block.get("quote", {}).get("rich_text", [])
            )
            markdown += f"> {text}\n\n"

        elif block_type == "divider":
            markdown += "---\n\n"

        elif block_type == "image":
            image_block = block.get("image", {})
            caption = convert_rich_text_to_markdown(image_block.get("caption", []))

            if image_block.get("type") == "external":
                url = image_block.get("external", {}).get("url", "")
                markdown += f"![{caption}]({url})\n\n"
            elif image_block.get("type") == "file":
                url = image_block.get("file", {}).get("url", "")
                markdown += f"![{caption}]({url})\n\n"

        # 하위 블록 처리 (토글 제외)
        if "children" in block and block_type != "toggle":
            inner_markdown = convert_blocks_to_markdown(block["children"])
            markdown += inner_markdown

    return markdown


def create_hugo_frontmatter(properties: Dict[str, Any]) -> str:
    """
    Notion 페이지 속성을 Hugo 프론트매터로 변환합니다.

    Args:
        properties: Notion 페이지 속성

    Returns:
        YAML 형식의 Hugo 프론트매터
    """
    frontmatter = []
    frontmatter.append("---")

    # 제목
    title = properties.get("title", "Untitled")
    # Remove markdown/HTML bold from title (for Notion->Hugo)
    import re

    title = re.sub(r"(\*\*|__|<b>|</b>|<strong>|</strong>)", "", title)
    frontmatter.append(f'title: "{title}"')

    # 날짜
    if "date" in properties:
        frontmatter.append(f'date: {properties["date"]}')

    # 마지막 수정일
    if "last_edited_time" in properties:
        frontmatter.append(f'lastmod: {properties["last_edited_time"]}')

    # 작성자
    if "author" in properties:
        frontmatter.append(f'author: "{properties["author"]}"')

    # 설명
    if "description" in properties:
        frontmatter.append(f'description: "{properties["description"]}"')

    # 태그
    if "tags" in properties and properties["tags"]:
        frontmatter.append("tags:")
        for tag in properties["tags"]:
            frontmatter.append(f'  - "{tag}"')

    # 카테고리
    if "categories" in properties and properties["categories"]:
        frontmatter.append("categories:")
        for category in properties["categories"]:
            frontmatter.append(f'  - "{category}"')

    # 초안 여부
    if "draft" in properties:
        frontmatter.append(f'draft: {str(properties["draft"]).lower()}')

    # Notion ID (메타데이터)
    if "id" in properties:
        frontmatter.append(f'notion_id: "{properties["id"]}"')

    frontmatter.append("---")

    return "\n".join(frontmatter)


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
