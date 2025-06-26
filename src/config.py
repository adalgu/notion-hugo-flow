import os
import yaml
from typing import Dict, List, Optional, TypedDict, Any
from dotenv import load_dotenv
from notion_client import Client


# 타입 정의
class PageMount(TypedDict):
    page_id: str
    target_folder: str


class DatabaseMount(TypedDict):
    database_id: str
    target_folder: str


class Mount(TypedDict):
    databases: List[DatabaseMount]
    pages: List[PageMount]


class FilenameConfig(TypedDict):
    format: str
    date_format: str
    korean_title: str


class Config(TypedDict):
    mount: Mount
    filename: Optional[FilenameConfig]


class UserMount(TypedDict):
    manual: bool
    page_url: Optional[str]
    databases: Optional[List[DatabaseMount]]
    pages: Optional[List[PageMount]]


class UserConfig(TypedDict):
    mount: UserMount


def load_config() -> Config:
    """
    설정 파일을 로드하고 설정 객체를 반환합니다.
    """
    # 환경 변수 로드
    load_dotenv()

    # 사용자 정의 설정 파일 로드
    default_config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "notion-hugo.config.yaml"
    )
    config_path = os.environ.get("NOTION_HUGO_CONFIG", default_config_path)

    with open(config_path, "r") as file:
        user_config = yaml.safe_load(file)

    config: Config = {
        "mount": {"databases": [], "pages": []},
        "filename": {
            "format": "uuid",  # 기본값은 기존 방식과 동일
            "date_format": "%Y-%m-%d",
            "korean_title": "slug",
        },
    }

    # 파일명 설정이 있으면 로드
    if "filename" in user_config:
        config["filename"].update(user_config["filename"])

    # 마운트 설정 구성
    if user_config.get("mount", {}).get("manual", True):
        if "databases" in user_config.get("mount", {}):
            for db in user_config["mount"]["databases"]:
                if not db.get("database_id"):
                    raise ValueError(
                        f"데이터베이스 ID가 {db['target_folder']}에 대해 설정되지 않았습니다. "
                        f"notion-hugo.config.yaml 파일을 확인하세요."
                    )
                config["mount"]["databases"].append(db)

        if "pages" in user_config.get("mount", {}):
            config["mount"]["pages"] = user_config["mount"]["pages"]
    else:
        if "page_url" not in user_config["mount"]:
            raise ValueError(
                "mount.manual이 False일 때는 page_url이 설정되어야 합니다."
            )

        url = user_config["mount"]["page_url"]
        # URL에서 페이지 ID 추출
        page_id = url.split("/")[-1]
        if len(page_id) < 32:
            raise ValueError(f"페이지 URL {url}이 유효하지 않습니다.")

        # NOTION_TOKEN 환경 변수 확인
        if not os.environ.get("NOTION_TOKEN"):
            raise ValueError("NOTION_TOKEN 환경 변수가 설정되지 않았습니다.")

        # Notion 클라이언트 생성
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))

        # 페이지의 하위 블록 조회
        blocks = notion.blocks.children.list(block_id=page_id)

        for block in blocks["results"]:
            if block["type"] == "child_database":
                config["mount"]["databases"].append(
                    {
                        "database_id": block["id"],
                        "target_folder": block["child_database"]["title"],
                    }
                )
            elif block["type"] == "child_page":
                config["mount"]["pages"].append(
                    {"page_id": block["id"], "target_folder": "."}
                )

    return config


def create_config_file(config: UserConfig):
    """
    설정 파일을 생성합니다.
    """
    default_config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "notion-hugo.config.yaml"
    )
    config_path = os.environ.get("NOTION_HUGO_CONFIG", default_config_path)

    with open(config_path, "w") as file:
        yaml.dump(config, file, default_flow_style=False)
