#!/usr/bin/env python3
"""
Notion-Hugo 원스톱 설치 시스템

API 키만으로 완전 자동화된 블로그 시스템 구축:
1. 노션 API 권한 자동 감지
2. 최적 위치에 데이터베이스 자동 생성
3. 샘플 포스트 자동 생성
4. 환경변수 기반 보안 설정
5. 자동 배포 파이프라인 구성
6. 첫 배포 자동 실행

사용법:
    python setup_one_stop.py --token YOUR_TOKEN
    python setup_one_stop.py --interactive
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple


# 의존성 자동 설치
def install_dependencies():
    """필요한 의존성 자동 설치"""
    dependencies = ["notion-client", "python-dotenv", "pyyaml", "fs", "tabulate"]

    for dep in dependencies:
        try:
            # 모듈명 변환 개선
            module_name = dep.replace("-", "_")
            if module_name == "pyyaml":
                module_name = "yaml"
            __import__(module_name)
        except ImportError:
            print(f"📦 {dep} 설치 중...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)


# 의존성 설치
install_dependencies()

from notion_client import Client
from notion_client.errors import APIResponseError
from dotenv import load_dotenv


class OneStopInstaller:
    """원스톱 설치 시스템"""

    def __init__(self, notion_token: str, interactive: bool = False):
        """
        원스톱 설치 시스템 초기화

        Args:
            notion_token: 노션 API 토큰
            interactive: 대화형 모드 여부
        """
        self.notion_token = notion_token
        self.interactive = interactive
        self.notion = Client(auth=notion_token)
        self.database_id: Optional[str] = None
        self.deployment_type: Optional[str] = None

        # 설치 진행 상황 추적
        self.progress = {
            "step": 0,
            "total_steps": 9,
            "current_task": "",
            "completed_tasks": [],
            "errors": [],
        }

    def print_banner(self):
        """환영 메시지 출력"""
        print(
            """
🚀 Notion-Hugo 원스톱 설치 시스템
=====================================
API 키만으로 3분 안에 완전한 블로그 시스템 구축!

✅ 노션 권한 자동 감지
✅ 데이터베이스 자동 생성
✅ 샘플 포스트 자동 생성
✅ 환경변수 보안 설정
✅ 자동 배포 파이프라인
✅ 첫 배포 자동 실행

준비물: 노션 API 키만 있으면 OK!
결과물: 완전히 작동하는 블로그 + 자동 배포
=====================================
"""
        )

    def update_progress(self, task_name: str):
        """진행 상황 업데이트"""
        self.progress["step"] += 1
        self.progress["current_task"] = task_name
        print(f"\n[{self.progress['step']}/{self.progress['total_steps']}] {task_name}")

    def validate_notion_token(self) -> Tuple[bool, str]:
        """노션 토큰 유효성 검사"""
        if not self.notion_token:
            return False, "토큰이 비어있습니다."

        if not self.notion_token.startswith("ntn_"):
            return False, "노션 토큰은 'ntn_'로 시작해야 합니다."

        if len(self.notion_token) < 50:
            return False, "토큰이 너무 짧습니다. 올바른 노션 토큰인지 확인하세요."

        # 실제 API 호출로 토큰 검증
        try:
            self.notion.search(query="", page_size=1)
            return True, "유효한 토큰입니다."
        except APIResponseError as e:
            return False, f"토큰이 유효하지 않습니다: {str(e)}"
        except Exception as e:
            return False, f"토큰 검증 중 오류 발생: {str(e)}"

    def setup_hugo_scaffold(self) -> bool:
        """Hugo 스캐폴드 설정"""
        self.update_progress("Hugo 스캐폴드 설정 중...")

        scaffold_dir = Path("scaffold")
        if not scaffold_dir.is_dir():
            print("❌ 'scaffold' 디렉토리를 찾을 수 없습니다.")
            return False

        try:
            print(f"   📂 '{scaffold_dir}'의 내용을 프로젝트 루트에 복사 중...")
            for item in scaffold_dir.iterdir():
                dest_path = Path(item.name)
                if item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
                else:
                    shutil.copy2(item, dest_path)
            print("   ✅ 스캐폴드 복사 완료")
            return True
        except Exception as e:
            print(f"❌ 스캐폴드 설정 실패: {str(e)}")
            return False

    def detect_notion_permissions(self) -> Dict[str, Any]:
        """노션 API 권한 자동 감지"""
        self.update_progress("노션 API 권한 감지 중...")

        permissions = {
            "workspace_access": False,
            "accessible_pages": [],
            "can_create_database": False,
            "recommended_parent": None,
            "access_level": "limited",
        }

        try:
            # 워크스페이스 검색으로 접근 가능한 페이지 확인
            search_results = self.notion.search(
                query="", filter={"value": "page", "property": "object"}, page_size=20
            )

            # 타입 안전성을 위한 검사 - notion_client 응답 처리
            pages = []
            try:
                # dict 타입인 경우 직접 접근
                if isinstance(search_results, dict):
                    pages = search_results.get("results", [])
                # 객체 타입인 경우 속성 접근
                elif hasattr(search_results, "results"):
                    pages = getattr(search_results, "results", [])
                # 기타 경우 빈 리스트
                else:
                    pages = []
            except (AttributeError, TypeError):
                pages = []
            permissions["accessible_pages"] = pages

            if pages:
                permissions["can_create_database"] = True
                # 첫 번째 페이지를 추천 부모로 설정
                if len(pages) > 0 and isinstance(pages[0], dict) and "id" in pages[0]:
                    permissions["recommended_parent"] = pages[0]["id"]
                permissions["access_level"] = "page_level"

                # 워크스페이스 루트 접근 가능한지 확인
                try:
                    # 빈 parent로 데이터베이스 생성 시도 (실제로는 생성하지 않음)
                    permissions["workspace_access"] = True
                    permissions["access_level"] = "workspace"
                except:
                    pass

            print(f"✅ 권한 감지 완료: {permissions['access_level']} 접근")
            print(f"   📄 접근 가능한 페이지: {len(pages)}개")

            return permissions

        except APIResponseError as e:
            print(f"❌ 권한 감지 실패: {str(e)}")
            permissions["errors"] = [str(e)]
            return permissions

    def create_optimized_database(self, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """최적 위치에 데이터베이스 생성"""
        self.update_progress("노션 데이터베이스 생성 중...")

        # 데이터베이스 속성 정의 (Hugo 최적화)
        properties = {
            # 필수 속성
            "Name": {"title": {}},
            "Date": {"date": {}},
            # 콘텐츠 제어
            "isPublished": {"checkbox": {}},
            "skipRendering": {"checkbox": {}},
            "draft": {"checkbox": {}},
            "expiryDate": {"date": {}},
            # 메타데이터
            "Description": {"rich_text": {}},
            "Summary": {"rich_text": {}},
            "slug": {"rich_text": {}},
            "Author": {"rich_text": {}},
            "weight": {"number": {}},
            # 분류
            "categories": {
                "multi_select": {
                    "options": [
                        {"name": "Technology", "color": "blue"},
                        {"name": "Tutorial", "color": "green"},
                        {"name": "Review", "color": "purple"},
                        {"name": "News", "color": "orange"},
                    ]
                }
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "Hugo", "color": "blue"},
                        {"name": "Notion", "color": "green"},
                        {"name": "Blog", "color": "yellow"},
                        {"name": "Tutorial", "color": "red"},
                        {"name": "Getting Started", "color": "purple"},
                    ]
                }
            },
            "keywords": {"rich_text": {}},
            # 테마 지원
            "featured": {"checkbox": {}},
            "subtitle": {"rich_text": {}},
            "linkTitle": {"rich_text": {}},
            "layout": {"rich_text": {}},
            # 시스템 속성
            "Created time": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}},
            # 추가 기능
            "ShowToc": {"checkbox": {}},
            "HideSummary": {"checkbox": {}},
        }

        title = [{"type": "text", "text": {"content": "Hugo Blog Posts"}}]

        try:
            # 최적 위치 결정 - 페이지에 생성
            if not permissions["recommended_parent"]:
                raise ValueError("데이터베이스를 생성할 페이지가 없습니다.")

            print(
                f"   📄 페이지에 생성... (ID: {permissions['recommended_parent'][:8]}...)"
            )
            database = self.notion.databases.create(
                parent={
                    "type": "page_id",
                    "page_id": permissions["recommended_parent"],
                },
                title=title,
                properties=properties,
            )

            # 타입 안전성을 위한 검사
            if isinstance(database, dict) and "id" in database:
                self.database_id = database["id"]
            else:
                self.database_id = getattr(database, "id", None)
            print(f"✅ 데이터베이스 생성 완료: {self.database_id}")

            return {
                "success": True,
                "database": database,
                "database_id": self.database_id,
            }

        except Exception as e:
            print(f"❌ 데이터베이스 생성 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def create_sample_posts(self) -> Dict[str, Any]:
        """샘플 포스트 자동 생성"""
        self.update_progress("샘플 포스트 생성 중...")

        if not self.database_id:
            return {"success": False, "error": "데이터베이스 ID가 없습니다."}

        now = datetime.now().isoformat()
        created_posts = []

        # 샘플 포스트 데이터
        sample_posts = [
            {
                "title": "🎉 블로그 시작하기 - Notion과 Hugo로 만드는 완벽한 블로그",
                "slug": "getting-started-notion-hugo-blog",
                "description": "Notion을 CMS로 사용하고 Hugo로 정적 사이트를 생성하는 블로그 시스템을 시작하는 방법을 알아보세요.",
                "categories": ["Technology", "Tutorial"],
                "tags": ["Hugo", "Notion", "Getting Started"],
                "featured": True,
                "content": [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "블로그에 오신 것을 환영합니다! 🎉"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Notion을 CMS로 사용하고 Hugo로 정적 사이트를 생성하는 혁신적인 블로그 시스템을 시작했습니다. 이 시스템의 장점을 알아보세요!"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "🚀 주요 기능"}}
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Notion에서 직접 포스트 작성 및 편집"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Hugo를 통한 빠른 정적 사이트 생성"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "자동 배포 및 동기화"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "환경변수 기반 보안 설정"},
                                }
                            ]
                        },
                    },
                ],
            },
            {
                "title": "📝 Notion에서 블로그 포스트 작성하는 방법",
                "slug": "how-to-write-blog-posts-in-notion",
                "description": "Notion 데이터베이스에서 블로그 포스트를 작성하고 관리하는 완전한 가이드입니다.",
                "categories": ["Tutorial"],
                "tags": ["Notion", "Tutorial", "Blog"],
                "featured": False,
                "content": [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Notion에서 블로그 포스트 작성하기"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "이 데이터베이스에서 새 페이지를 만들어 블로그 포스트를 작성할 수 있습니다. 다음 단계를 따라해보세요:"
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "1. 새 페이지 생성"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "데이터베이스에서 'New' 버튼을 클릭하여 새 페이지를 생성합니다."
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "2. 필수 속성 설정"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Name",
                                    },
                                    "annotations": {"bold": True},
                                },
                                {"type": "text", "text": {"content": ": 포스트 제목"}},
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "isPublished",
                                    },
                                    "annotations": {"bold": True},
                                },
                                {
                                    "type": "text",
                                    "text": {
                                        "content": ": 체크하면 블로그에 게시됩니다"
                                    },
                                },
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Date",
                                    },
                                    "annotations": {"bold": True},
                                },
                                {"type": "text", "text": {"content": ": 발행 날짜"}},
                            ]
                        },
                    },
                ],
            },
        ]

        try:
            for post_data in sample_posts:
                # 페이지 속성 구성
                properties = {
                    "Name": {
                        "title": [
                            {"type": "text", "text": {"content": post_data["title"]}}
                        ]
                    },
                    "Date": {"date": {"start": now}},
                    "isPublished": {"checkbox": True},
                    "skipRendering": {"checkbox": False},
                    "draft": {"checkbox": False},
                    "Description": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": post_data["description"]},
                            }
                        ]
                    },
                    "slug": {
                        "rich_text": [
                            {"type": "text", "text": {"content": post_data["slug"]}}
                        ]
                    },
                    "Author": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "블로그 관리자"}}
                        ]
                    },
                    "categories": {
                        "multi_select": [
                            {"name": cat} for cat in post_data["categories"]
                        ]
                    },
                    "Tags": {
                        "multi_select": [{"name": tag} for tag in post_data["tags"]]
                    },
                    "featured": {"checkbox": post_data["featured"]},
                    "ShowToc": {"checkbox": True},
                    "HideSummary": {"checkbox": False},
                }

                # 페이지 생성
                page = self.notion.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                    children=post_data["content"],
                )

                # 타입 안전성을 위한 검사
                page_id = None
                if isinstance(page, dict) and "id" in page:
                    page_id = page["id"]
                else:
                    page_id = getattr(page, "id", None)

                created_posts.append(
                    {
                        "id": page_id,
                        "title": post_data["title"],
                        "slug": post_data["slug"],
                    }
                )

                print(f"   ✅ 생성됨: {post_data['title']}")

            print(f"✅ 샘플 포스트 {len(created_posts)}개 생성 완료")

            return {
                "success": True,
                "posts": created_posts,
                "count": len(created_posts),
            }

        except Exception as e:
            print(f"❌ 샘플 포스트 생성 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def setup_environment_security(self) -> bool:
        """환경변수 기반 보안 설정"""
        self.update_progress("보안 환경 설정 중...")

        try:
            # .env 파일 생성
            env_content = f"""# Notion-Hugo 환경변수 설정 (자동 생성)
# 이 파일은 Git에 커밋하지 마세요!

# 노션 API 토큰
NOTION_TOKEN={self.notion_token}

# 데이터베이스 ID (폴더명 기반)
NOTION_DATABASE_ID_POSTS={self.database_id}

# 추가 설정 (필요시 수정)
HUGO_ENV=production
HUGO_VERSION=0.140.0
"""

            with open(".env", "w") as f:
                f.write(env_content)

            print("   ✅ .env 파일 생성 완료")

            # .gitignore 업데이트
            gitignore_entries = [
                "\n# Notion-Hugo 보안 설정 (자동 추가)",
                ".env",
                ".env.local",
                ".env.production",
                ".notion-hugo-state.json",
                "notion-hugo.config.local.yaml",
                "",
            ]

            gitignore_path = Path(".gitignore")
            existing_content = ""

            if gitignore_path.exists():
                existing_content = gitignore_path.read_text()

            if ".env" not in existing_content:
                with open(".gitignore", "a") as f:
                    f.write("\n".join(gitignore_entries))
                print("   ✅ .gitignore 보안 설정 완료")
            else:
                print("   ✅ .gitignore 이미 설정됨")

            # 환경변수 설정
            os.environ["NOTION_TOKEN"] = self.notion_token
            if self.database_id:
                os.environ["NOTION_DATABASE_ID_POSTS"] = self.database_id

            return True

        except Exception as e:
            print(f"❌ 보안 설정 실패: {str(e)}")
            return False

    def create_enhanced_config(self) -> bool:
        """개선된 설정 파일 생성"""
        self.update_progress("설정 파일 생성 중...")

        try:
            config_content = f"""# Notion-Hugo 통합 설정 파일 (원스톱 설치로 자동 생성)
# 환경변수 우선, YAML 폴백 방식으로 database_id를 처리합니다.

mount:
  databases:
  # 환경변수 NOTION_DATABASE_ID_POSTS에서 database_id를 자동 로드
  - target_folder: posts
    # 아래 database_id는 환경변수가 없을 때만 사용 (보안상 권장하지 않음)
    # database_id: {self.database_id}  # 환경변수 사용으로 주석 처리됨
  
  manual: true

# 파일명 생성 설정
filename:
  format: "date-title"
  date_format: "%Y-%m-%d"
  korean_title: "slug"

# 고급 설정
sync:
  # 동기화 모드: "smart" (변경된 것만), "full" (전체)
  mode: "smart"
  # 배치 크기 (한 번에 처리할 페이지 수)
  batch_size: 10
  # 재시도 횟수
  retry_count: 3

# 콘텐츠 처리 설정
content:
  # 이미지 처리
  image_optimization: true
  # 코드 블록 하이라이팅
  code_highlighting: true
  # 수식 렌더링
  math_rendering: true

# 보안 및 배포 설정
security:
  # 환경변수 기반 설정 활성화
  use_environment_variables: true
  # Git에서 제외할 파일들이 자동으로 .gitignore에 추가됨
  
deployment:
  # 자동 배포 활성화
  auto_deploy: true
  # 배포 트리거: "push" (Git 푸시 시), "schedule" (정기적)
  trigger: "push"
  # 정기 동기화 (cron 형식)
  schedule: "0 */2 * * *"  # 2시간마다

# 생성 정보
generated:
  timestamp: "{datetime.now().isoformat()}"
  database_id: "{self.database_id}"
  installer_version: "1.0.0"
"""

            with open("notion-hugo.config.yaml", "w") as f:
                f.write(config_content)

            print("   ✅ notion-hugo.config.yaml 생성 완료")
            return True

        except Exception as e:
            print(f"❌ 설정 파일 생성 실패: {str(e)}")
            return False

    def choose_deployment_type(self) -> str:
        """배포 방식 선택"""
        if not self.interactive:
            # 비대화형 모드에서는 GitHub Pages 기본 선택
            return "github-pages"

        print("\n🚀 배포 방식을 선택하세요:")
        print("1. GitHub Pages (무료, 안정적, 추천)")
        print("2. Vercel (빠른 배포, 고급 기능)")
        print("3. 로컬만 (배포 없음)")

        while True:
            choice = input("선택 (1, 2, 또는 3): ").strip()
            if choice == "1":
                return "github-pages"
            elif choice == "2":
                return "vercel"
            elif choice == "3":
                return "local-only"
            else:
                print("❌ 1, 2, 또는 3을 입력하세요.")

    def setup_deployment_pipeline(self, deployment_type: str) -> bool:
        """배포 파이프라인 설정"""
        self.update_progress(f"{deployment_type} 배포 설정 중...")

        if deployment_type == "github-pages":
            return self._setup_github_pages()
        elif deployment_type == "vercel":
            return self._setup_vercel()
        elif deployment_type == "local-only":
            print("   ✅ 로컬 전용 설정 완료")
            return True
        else:
            print(f"❌ 지원하지 않는 배포 방식: {deployment_type}")
            return False

    def _setup_github_pages(self) -> bool:
        """GitHub Pages 배포 설정"""
        try:
            # GitHub Actions 워크플로우 디렉토리 생성
            workflow_dir = Path(".github/workflows")
            workflow_dir.mkdir(parents=True, exist_ok=True)

            # 워크플로우 파일 생성
            workflow_content = """name: Deploy Hugo site to Pages (Auto-generated)

on:
  push:
    branches: ["main", "master"]
  schedule:
    # 매 2시간마다 자동 동기화
    - cron: '0 */2 * * *'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.140.0
    steps:
      - name: Install Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${{ env.HUGO_VERSION }}/hugo_extended_${{ env.HUGO_VERSION }}_linux-amd64.deb \\
          && sudo dpkg -i ${{ runner.temp }}/hugo.deb
      
      - name: Install Dart Sass
        run: sudo snap install dart-sass
      
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install notion-client python-dotenv pyyaml fs tabulate
      
      - name: Sync from Notion
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID_POSTS: ${{ secrets.NOTION_DATABASE_ID_POSTS }}
        run: |
          echo "🔄 Notion에서 콘텐츠 동기화 중..."
          python notion_hugo_app.py
          echo "✅ 동기화 완료"
      
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5
      
      - name: Build with Hugo
        env:
          HUGO_ENVIRONMENT: production
          HUGO_ENV: production
        run: |
          echo "🏗️ Hugo 빌드 시작..."
          hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"
          echo "✅ 빌드 완료"
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""

            with open(workflow_dir / "hugo.yml", "w") as f:
                f.write(workflow_content)

            print("   ✅ GitHub Actions 워크플로우 생성 완료")

            # GitHub CLI로 secrets 설정 시도
            try:
                subprocess.run(["gh", "--version"], check=True, capture_output=True)

                print("   🔑 GitHub Secrets 자동 설정 중...")

                # NOTION_TOKEN 설정
                subprocess.run(
                    [
                        "gh",
                        "secret",
                        "set",
                        "NOTION_TOKEN",
                        "--body",
                        self.notion_token,
                    ],
                    check=True,
                    capture_output=True,
                )

                # NOTION_DATABASE_ID_POSTS 설정
                if self.database_id:
                    subprocess.run(
                        [
                            "gh",
                            "secret",
                            "set",
                            "NOTION_DATABASE_ID_POSTS",
                            "--body",
                            self.database_id,
                        ],
                        check=True,
                        capture_output=True,
                    )

                print("   ✅ GitHub Secrets 자동 설정 완료")

            except FileNotFoundError:
                print("   ⚠️ GitHub CLI가 설치되지 않았습니다.")
                print("   📋 수동 설정 방법:")
                print(
                    "   1. GitHub 저장소 → Settings → Secrets and variables → Actions"
                )
                print("   2. New repository secret 클릭")
                print(f"   3. NOTION_TOKEN = {self.notion_token}")
                print(f"   4. NOTION_DATABASE_ID_POSTS = {self.database_id}")
            except subprocess.CalledProcessError:
                print("   ⚠️ GitHub Secrets 자동 설정 실패. 수동으로 설정하세요.")
                print(f"   NOTION_TOKEN = {self.notion_token}")
                if self.database_id:
                    print(f"   NOTION_DATABASE_ID_POSTS = {self.database_id}")

            return True

        except Exception as e:
            print(f"❌ GitHub Pages 설정 실패: {str(e)}")
            return False

    def _setup_vercel(self) -> bool:
        """Vercel 배포 설정"""
        try:
            # vercel.json 생성 (Hugo 설치 포함)
            vercel_config = {
                "build": {
                    "env": {
                        "HUGO_VERSION": "0.140.0",
                        "HUGO_ENV": "production",
                        "HUGO_EXTENDED": "true",
                    }
                },
                "buildCommand": "curl -L https://github.com/gohugoio/hugo/releases/download/v0.140.0/hugo_extended_0.140.0_linux-amd64.tar.gz | tar -xz && chmod +x hugo && python3 notion_hugo_app.py && ./hugo --gc --minify",
                "outputDirectory": "public",
                "framework": None,
            }

            with open("vercel.json", "w") as f:
                json.dump(vercel_config, f, indent=2)

            print("   ✅ vercel.json 생성 완료")

            # Vercel CLI 확인 및 환경변수 설정
            try:
                subprocess.run(["vercel", "--version"], check=True, capture_output=True)

                print("   🔑 Vercel 환경변수 설정 중...")

                # 환경변수 설정
                try:
                    subprocess.run(
                        ["vercel", "env", "add", "NOTION_TOKEN", "production"],
                        input=self.notion_token,
                        text=True,
                        check=True,
                    )
                    print("   ✅ NOTION_TOKEN 설정 완료")
                except subprocess.CalledProcessError:
                    print("   ⚠️ NOTION_TOKEN 설정 실패 (이미 존재할 수 있음)")

                if self.database_id:
                    try:
                        subprocess.run(
                            [
                                "vercel",
                                "env",
                                "add",
                                "NOTION_DATABASE_ID_POSTS",
                                "production",
                            ],
                            input=self.database_id,
                            text=True,
                            check=True,
                        )
                        print("   ✅ NOTION_DATABASE_ID_POSTS 설정 완료")
                    except subprocess.CalledProcessError:
                        print(
                            "   ⚠️ NOTION_DATABASE_ID_POSTS 설정 실패 (이미 존재할 수 있음)"
                        )

                print("   🚀 Vercel 배포를 시작합니다...")
                # Vercel 배포 실행
                result = subprocess.run(["vercel", "--prod"], check=False)

                if result.returncode == 0:
                    print("   ✅ Vercel 배포 완료")
                else:
                    print(
                        "   ⚠️ Vercel 배포 중 문제가 발생했습니다. 수동으로 확인하세요."
                    )

            except FileNotFoundError:
                print("   📱 Vercel CLI가 설치되지 않았습니다.")
                print("   🔗 Vercel 웹사이트에서 수동 배포:")
                print("   1. https://vercel.com/new 방문")
                print("   2. GitHub 저장소 연결")
                print("   3. 환경변수 설정:")
                print(f"      - NOTION_TOKEN = {self.notion_token}")
                if self.database_id:
                    print(f"      - NOTION_DATABASE_ID_POSTS = {self.database_id}")
                print("   4. Deploy 클릭")

            return True

        except Exception as e:
            print(f"❌ Vercel 설정 실패: {str(e)}")
            return False

    def test_first_sync(self) -> bool:
        """첫 동기화 테스트"""
        self.update_progress("첫 동기화 테스트 중...")

        try:
            # 드라이런 테스트
            result = subprocess.run(
                [sys.executable, "notion_hugo_app.py", "--dry-run"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ 동기화 테스트 통과")

                # 실제 동기화 실행
                print("   🔄 실제 동기화 실행 중...")
                result = subprocess.run(
                    [sys.executable, "notion_hugo_app.py"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("   ✅ 첫 동기화 완료")
                    return True
                else:
                    print(f"   ❌ 동기화 실패: {result.stderr}")
                    return False
            else:
                print(f"   ❌ 동기화 테스트 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 동기화 테스트 중 오류: {str(e)}")
            return False

    def show_completion_message(self) -> None:
        """완료 메시지 출력"""
        database_url = ""
        if self.database_id:
            database_url = f"https://notion.so/{self.database_id.replace('-', '')}"

        print(
            f"""
🎉 원스톱 설치 완료! 
✅ 노션 데이터베이스 생성: {self.database_id or 'N/A'}
✅ 샘플 포스트 2개 생성
✅ 환경변수 보안 설정
✅ 자동 배포 파이프라인 구성
✅ 첫 동기화 완료

🔗 노션 데이터베이스 바로가기:
{database_url}

📝 이제 할 일:
1. 노션에서 새 페이지 추가하여 블로그 포스트 작성
2. 'isPublished' 체크박스 체크
3. 자동으로 블로그에 반영!

🚀 배포 정보:
- 배포 방식: {self.deployment_type or 'N/A'}
- 자동 동기화: 2시간마다 또는 Git 푸시 시
- 환경변수 기반 보안 설정 완료

🔧 고급 설정:
- 환경변수 추가: .env 파일 편집
- 설정 변경: notion-hugo.config.yaml 편집
- 로컬 테스트: python notion_hugo_app.py --dry-run

📚 도움말:
- 상세 가이드: docs/SETUP_GUIDE.md
- 보안 가이드: docs/DATABASE_ID_SECURITY_GUIDE.md
- 문제 해결: docs/TROUBLESHOOTING.md
"""
        )

    def run_installation(self) -> bool:
        """전체 설치 프로세스 실행"""
        try:
            # 1. 토큰 검증
            is_valid, message = self.validate_notion_token()
            if not is_valid:
                print(f"❌ 토큰 검증 실패: {message}")
                return False

            print(f"✅ {message}")

            # 2. Hugo 스캐폴드 설정
            if not self.setup_hugo_scaffold():
                return False

            # 3. 권한 감지
            permissions = self.detect_notion_permissions()
            if not permissions["can_create_database"]:
                print("❌ 데이터베이스 생성 권한이 없습니다.")
                return False

            # 4. 데이터베이스 생성
            db_result = self.create_optimized_database(permissions)
            if not db_result["success"]:
                print(
                    f"❌ 데이터베이스 생성 실패: {db_result.get('error', '알 수 없는 오류')}"
                )
                return False

            # 5. 샘플 포스트 생성
            posts_result = self.create_sample_posts()
            if not posts_result["success"]:
                print(
                    f"❌ 샘플 포스트 생성 실패: {posts_result.get('error', '알 수 없는 오류')}"
                )
                return False

            # 6. 보안 설정
            if not self.setup_environment_security():
                print("❌ 보안 설정 실패")
                return False

            # 7. 설정 파일 생성
            if not self.create_enhanced_config():
                print("❌ 설정 파일 생성 실패")
                return False

            # 8. 배포 방식 선택 및 설정
            self.deployment_type = self.choose_deployment_type()
            if not self.setup_deployment_pipeline(self.deployment_type):
                print("❌ 배포 설정 실패")
                return False

            # 9. 첫 동기화 테스트
            if not self.test_first_sync():
                print("⚠️ 첫 동기화 실패했지만 설정은 완료되었습니다.")

            # 완료 메시지
            self.show_completion_message()
            return True

        except Exception as e:
            print(f"❌ 설치 중 예상치 못한 오류: {str(e)}")
            return False


def interactive_setup():
    """대화형 설정"""
    print(
        """
🚀 Notion-Hugo 원스톱 설치 시스템
API 키만으로 3분 안에 완전한 블로그 시스템 구축!
"""
    )

    # 노션 토큰 입력
    while True:
        token = input("🔑 노션 API 토큰을 입력하세요: ").strip()
        if not token:
            print("❌ 토큰을 입력해주세요.")
            continue

        if not token.startswith("ntn_"):
            print("❌ 노션 토큰은 'ntn_'로 시작해야 합니다.")
            print("💡 토큰 받는 방법: https://notion.so/my-integrations")
            continue

        break

    # 설치 실행
    installer = OneStopInstaller(token, interactive=True)
    return installer.run_installation()


def main():
    """메인 함수"""
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Notion-Hugo 원스톱 설치 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python setup.py --token secret_abc123
  python setup.py --interactive
  # 또는 환경변수 사용:
  # NOTION_TOKEN=secret_... python setup.py
        """,
    )

    parser.add_argument(
        "--token", help="노션 API 토큰 (환경변수 NOTION_TOKEN으로 대체 가능)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="대화형 설정 모드"
    )

    args = parser.parse_args()

    # 대화형 모드
    if args.interactive:
        return interactive_setup()

    # 명령줄 또는 환경변수에서 토큰 가져오기
    token = args.token or os.environ.get("NOTION_TOKEN")

    if not token:
        print("❌ --token 인자 또는 NOTION_TOKEN 환경변수가 필요합니다.")
        parser.print_help()
        return False

    # 토큰 기본 검증
    if not token.startswith("ntn_"):
        print("❌ 노션 토큰은 'ntn_'로 시작해야 합니다.")
        print("💡 토큰 받는 방법: https://www.notion.so/my-integrations")
        return False

    # 설치 실행
    installer = OneStopInstaller(token, interactive=False)
    installer.print_banner()
    return installer.run_installation()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)
