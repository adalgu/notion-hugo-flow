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


def get_database_id_from_env(env_key: str, fallback_id: Optional[str] = None) -> str:
    """
    환경변수에서 database_id를 가져오고, 없으면 fallback 사용

    Args:
        env_key: 환경변수 키 (예: NOTION_DATABASE_ID_POSTS)
        fallback_id: YAML에서 가져온 fallback ID

    Returns:
        database_id
    """
    env_id = os.environ.get(env_key)
    if env_id:
        print(f"[Info] 환경변수 {env_key}에서 database_id 로드: {env_id}")
        return env_id
    elif fallback_id:
        print(f"[Info] YAML 설정에서 database_id 로드: {fallback_id}")
        return fallback_id
    else:
        raise ValueError(
            f"database_id를 찾을 수 없습니다. 환경변수 {env_key} 또는 YAML 설정을 확인하세요."
        )


def load_config() -> Config:
    """
    설정 파일을 로드하고 설정 객체를 반환합니다.
    환경변수 우선, YAML 폴백 방식으로 database_id를 처리합니다.
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
    if "filename" in user_config and config["filename"]:
        config["filename"].update(user_config["filename"])

    # 마운트 설정 구성
    if user_config["mount"]["manual"]:
        if "databases" in user_config["mount"]:
            # 각 데이터베이스에 대해 환경변수 우선 처리
            for i, db_config in enumerate(user_config["mount"]["databases"]):
                # 환경변수 키 생성 (예: NOTION_DATABASE_ID_POSTS, NOTION_DATABASE_ID_1)
                target_folder = db_config.get("target_folder", "posts")
                env_key = f"NOTION_DATABASE_ID_{target_folder.upper()}"

                # 인덱스 기반 환경변수도 지원 (여러 데이터베이스용)
                env_key_indexed = f"NOTION_DATABASE_ID_{i}"

                # 환경변수에서 ID 찾기 (폴더명 기반 -> 인덱스 기반 -> YAML 폴백)
                database_id = (
                    os.environ.get(env_key)
                    or os.environ.get(env_key_indexed)
                    or db_config.get("database_id")
                )

                if not database_id:
                    raise ValueError(
                        f"database_id를 찾을 수 없습니다. 환경변수 {env_key} 또는 YAML 설정을 확인하세요."
                    )

                config["mount"]["databases"].append(
                    {"database_id": database_id, "target_folder": target_folder}
                )

                # 환경변수 사용 여부 로깅
                if os.environ.get(env_key):
                    print(f"[Info] 환경변수 {env_key}에서 database_id 로드")
                elif os.environ.get(env_key_indexed):
                    print(f"[Info] 환경변수 {env_key_indexed}에서 database_id 로드")
                else:
                    print(f"[Info] YAML 설정에서 database_id 로드")

        if "pages" in user_config["mount"]:
            config["mount"]["pages"] = user_config["mount"]["pages"]
    else:
        # 기존 page_url 기반 로직 유지
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
        blocks_response = notion.blocks.children.list(block_id=page_id)
        blocks_data = (
            blocks_response.get("results", [])
            if isinstance(blocks_response, dict)
            else []
        )

        for block in blocks_data:
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


def generate_env_template():
    """
    .env.sample 파일을 생성하여 사용자가 쉽게 환경변수를 설정할 수 있도록 합니다.
    """
    env_template = """# Notion API Token (필수)
NOTION_TOKEN=your_notion_token_here

# Database IDs (선택사항 - YAML 설정 대신 사용 가능)
# 폴더명 기반 환경변수 (추천)
NOTION_DATABASE_ID_POSTS=your_database_id_for_posts
# NOTION_DATABASE_ID_DOCS=your_database_id_for_docs

# 인덱스 기반 환경변수 (여러 데이터베이스용)
# NOTION_DATABASE_ID_0=your_first_database_id
# NOTION_DATABASE_ID_1=your_second_database_id

# 배포 환경 설정
# HUGO_ENV=production
# HUGO_VERSION=0.140.0
"""

    with open(".env.sample", "w") as f:
        f.write(env_template)

    print("[Info] .env.sample 파일이 생성되었습니다.")
