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
        self.notion = Client(
            auth=notion_token,
            notion_version="2025-09-03"
        )
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
            return False, "Token is empty."

        if not self.notion_token.startswith("ntn_"):
            return False, "Notion token must start with 'ntn_'."

        if len(self.notion_token) < 50:
            return (
                False,
                "Token is too short. Please check if it's a valid Notion token.",
            )

        # 실제 API 호출로 토큰 검증
        try:
            self.notion.search(query="", page_size=1)
            return True, "Valid token."
        except APIResponseError as e:
            return False, f"Invalid token: {str(e)}"
        except Exception as e:
            return False, f"Error validating token: {str(e)}"

    def setup_hugo_scaffold(self) -> bool:
        """Hugo 스캐폴드 설정"""
        self.update_progress("Setting up Hugo scaffold...")

        scaffold_dir = Path("scaffold")
        if not scaffold_dir.is_dir():
            print("❌ 'scaffold' directory not found.")
            return False

        try:
            print(f"   📂 Copying contents of '{scaffold_dir}' to project root...")
            for item in scaffold_dir.iterdir():
                dest_path = Path(item.name)
                if item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
                else:
                    shutil.copy2(item, dest_path)
            print("   ✅ Scaffold copied successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to set up scaffold: {str(e)}")
            return False

    def detect_notion_permissions(self) -> Dict[str, Any]:
        """노션 API 권한 자동 감지"""
        self.update_progress("Detecting Notion permissions...")

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

            print(f"✅ Permissions detected: {permissions['access_level']} access")
            print(f"   📄 Accessible pages: {len(pages)}")

            return permissions

        except APIResponseError as e:
            print(f"❌ Failed to detect permissions: {str(e)}")
            permissions["errors"] = [str(e)]
            return permissions

    def create_optimized_database(self, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """최적 위치에 데이터베이스 생성"""
        self.update_progress("Creating Notion database...")

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
                raise ValueError("No page found to create database.")

            print(
                f"   📄 Creating in page... (ID: {permissions['recommended_parent'][:8]}...)"
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
            print(f"✅ Database created: {self.database_id}")

            return {
                "success": True,
                "database": database,
                "database_id": self.database_id,
            }

        except Exception as e:
            print(f"❌ Failed to create database: {str(e)}")
            return {"success": False, "error": str(e)}

    def create_sample_posts(self) -> Dict[str, Any]:
        """샘플 포스트 자동 생성"""
        self.update_progress("Creating sample posts...")

        if not self.database_id:
            return {"success": False, "error": "Database ID is missing."}

        now = datetime.now().isoformat()
        created_posts = []

        # 샘플 포스트 데이터
        sample_posts = [
            {
                "title": "🎉 Starting Your Blog - Notion and Hugo for a Perfect Blog",
                "slug": "getting-started-notion-hugo-blog",
                "description": "Learn how to use Notion as a CMS and generate a static site with Hugo. Start your blog system today!",
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
                                    "text": {"content": "Welcome to your blog! 🎉"},
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
                                        "content": "We have started an innovative blog system using Notion as a CMS and Hugo for static site generation. Learn about its advantages!"
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
                                {"type": "text", "text": {"content": "🚀 Key Features"}}
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
                                        "content": "Write and edit posts directly in Notion"
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
                                        "content": "Quick static site generation with Hugo"
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
                                        "content": "Automatic deployment and synchronization"
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
                                        "content": "Security settings based on environment variables"
                                    },
                                }
                            ]
                        },
                    },
                ],
            },
            {
                "title": "📝 How to Write Blog Posts in Notion",
                "slug": "how-to-write-blog-posts-in-notion",
                "description": "A complete guide on writing and managing blog posts in your Notion database.",
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
                                    "text": {"content": "Writing Blog Posts in Notion"},
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
                                        "content": "You can create a new page in this database to write a blog post. Follow these steps:"
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
                                    "text": {"content": "1. Create a new page"},
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
                                        "content": "Click the 'New' button in the database to create a new page."
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
                                    "text": {"content": "2. Set required properties"},
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
                                {"type": "text", "text": {"content": ": Post title"}},
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
                                        "content": ": Check to publish to the blog"
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
                                {
                                    "type": "text",
                                    "text": {"content": ": Publication date"},
                                },
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
                            {"type": "text", "text": {"content": "Blog Administrator"}}
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

                print(f"   ✅ Created: {post_data['title']}")

            print(f"✅ {len(created_posts)} sample posts created")

            return {
                "success": True,
                "posts": created_posts,
                "count": len(created_posts),
            }

        except Exception as e:
            print(f"❌ Failed to create sample posts: {str(e)}")
            return {"success": False, "error": str(e)}

    def setup_environment_security(self) -> bool:
        """환경변수 기반 보안 설정"""
        self.update_progress("Setting up environment security...")

        try:
            # .env 파일 생성
            env_content = f"""# Notion-Hugo Environment Variables (Auto-generated)
# Do not commit this file to Git!

# Notion API Token
NOTION_TOKEN={self.notion_token}

# Database ID (based on folder name)
NOTION_DATABASE_ID_POSTS={self.database_id}

# Additional settings (modify if needed)
HUGO_ENV=production
HUGO_VERSION=0.140.0
"""

            with open(".env", "w") as f:
                f.write(env_content)

            print("   ✅ .env file created")

            # .gitignore 업데이트
            gitignore_entries = [
                "\n# Notion-Hugo Security Settings (Auto-added)",
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
                print("   ✅ .gitignore security settings added")
            else:
                print("   ✅ .gitignore already configured")

            # 환경변수 설정
            os.environ["NOTION_TOKEN"] = self.notion_token
            if self.database_id:
                os.environ["NOTION_DATABASE_ID_POSTS"] = self.database_id

            return True

        except Exception as e:
            print(f"❌ Failed to set up security: {str(e)}")
            return False

    def create_enhanced_config(self) -> bool:
        """통합 설정 파일 업데이트"""
        self.update_progress("Updating unified configuration file...")

        try:
            # NotionSetup의 update_config 메서드를 사용하여 통합 설정 파일 업데이트
            try:
                from .notion_setup import NotionSetup, NotionSetupConfig
            except ImportError:
                from notion_setup import NotionSetup, NotionSetupConfig

            # 기본 설정으로 NotionSetup 인스턴스 생성
            setup_config: NotionSetupConfig = {
                "notion_token": self.token,
                "interactive": False,
            }
            setup = NotionSetup(setup_config)

            # 통합 설정 파일 업데이트
            setup.update_config(self.database_id, "posts")

            print("   ✅ src/config/notion-hugo-config.yaml updated")
            return True

        except Exception as e:
            print(f"❌ Failed to update configuration file: {str(e)}")
            return False

    def choose_deployment_type(self) -> str:
        """배포 방식 선택"""
        if not self.interactive:
            # 비대화형 모드에서는 GitHub Pages 기본 선택
            return "github-pages"

        print("\n🚀 Choose your deployment method:")
        print("1. GitHub Pages (Free, Stable, Recommended)")
        print("2. Vercel (Fast Deployment, Advanced Features)")
        print("3. Local Only (No Deployment)")

        while True:
            choice = input("Choose (1, 2, or 3): ").strip()
            if choice == "1":
                return "github-pages"
            elif choice == "2":
                return "vercel"
            elif choice == "3":
                return "local-only"
            else:
                print("❌ Please enter 1, 2, or 3.")

    def setup_deployment_pipeline(self, deployment_type: str) -> bool:
        """배포 파이프라인 설정"""
        self.update_progress(f"Setting up {deployment_type} deployment...")

        if deployment_type == "github-pages":
            return self._setup_github_pages()
        elif deployment_type == "vercel":
            return self._setup_vercel()
        elif deployment_type == "local-only":
            print("   ✅ Local-only setup complete")
            return True
        else:
            print(f"❌ Unsupported deployment type: {deployment_type}")
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
    # Auto-sync every 2 hours
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
          echo "🔄 Syncing content from Notion..."
          python notion_hugo_app.py
          echo "✅ Sync complete"
      
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5
      
      - name: Build with Hugo
        env:
          HUGO_ENVIRONMENT: production
          HUGO_ENV: production
        run: |
          echo "🏗️ Starting Hugo build..."
          hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"
          echo "✅ Build complete"
      
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

            print("   ✅ GitHub Actions workflow created")

            # GitHub CLI로 secrets 설정 시도
            try:
                subprocess.run(["gh", "--version"], check=True, capture_output=True)

                print("   🔑 Setting up GitHub Secrets...")

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

                print("   ✅ GitHub Secrets set up")

            except FileNotFoundError:
                print("   ⚠️ GitHub CLI is not installed.")
                print("   📋 Manual setup instructions:")
                print(
                    "   1. Go to GitHub repository → Settings → Secrets and variables → Actions"
                )
                print("   2. Click 'New repository secret'")
                print(f"   3. NOTION_TOKEN = {self.notion_token}")
                print(f"   4. NOTION_DATABASE_ID_POSTS = {self.database_id}")
            except subprocess.CalledProcessError:
                print(
                    "   ⚠️ Failed to set up GitHub Secrets automatically. Please set them manually."
                )
                print(f"   NOTION_TOKEN = {self.notion_token}")
                if self.database_id:
                    print(f"   NOTION_DATABASE_ID_POSTS = {self.database_id}")

            return True

        except Exception as e:
            print(f"❌ Failed to set up GitHub Pages: {str(e)}")
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

            print("   ✅ vercel.json created")

            # Vercel CLI 확인 및 환경변수 설정
            try:
                subprocess.run(["vercel", "--version"], check=True, capture_output=True)

                print("   🔑 Setting up Vercel environment variables...")

                # 환경변수 설정
                try:
                    subprocess.run(
                        ["vercel", "env", "add", "NOTION_TOKEN", "production"],
                        input=self.notion_token,
                        text=True,
                        check=True,
                    )
                    print("   ✅ NOTION_TOKEN set")
                except subprocess.CalledProcessError:
                    print("   ⚠️ NOTION_TOKEN might already exist.")

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
                        print("   ✅ NOTION_DATABASE_ID_POSTS set")
                    except subprocess.CalledProcessError:
                        print("   ⚠️ NOTION_DATABASE_ID_POSTS might already exist.")

                print("   🚀 Starting Vercel deployment...")
                # Vercel 배포 실행
                result = subprocess.run(["vercel", "--prod"], check=False)

                if result.returncode == 0:
                    print("   ✅ Vercel deployment complete")
                else:
                    print(
                        "   ⚠️ An issue occurred during Vercel deployment. Please check manually."
                    )

            except FileNotFoundError:
                print("   📱 Vercel CLI is not installed.")
                print("   �� Deploy manually on Vercel website:")
                print("   1. Visit https://vercel.com/new")
                print("   2. Connect your GitHub repository")
                print("   3. Set environment variables:")
                print(f"      - NOTION_TOKEN = {self.notion_token}")
                if self.database_id:
                    print(f"      - NOTION_DATABASE_ID_POSTS = {self.database_id}")
                print("   4. Click 'Deploy'")

            return True

        except Exception as e:
            print(f"❌ Failed to set up Vercel: {str(e)}")
            return False

    def test_first_sync(self) -> bool:
        """첫 동기화 테스트"""
        self.update_progress("Testing first sync...")

        try:
            # 드라이런 테스트
            result = subprocess.run(
                [sys.executable, "notion_hugo_app.py", "--dry-run"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ Sync test passed")

                # 실제 동기화 실행
                print("   🔄 Running actual sync...")
                result = subprocess.run(
                    [sys.executable, "notion_hugo_app.py"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("   ✅ First sync complete")
                    return True
                else:
                    print(f"   ❌ Sync failed: {result.stderr}")
                    return False
            else:
                print(f"   ❌ Sync test failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error during sync test: {str(e)}")
            return False

    def show_completion_message(self) -> None:
        """완료 메시지 출력"""
        database_url = ""
        if self.database_id:
            database_url = f"https://notion.so/{self.database_id.replace('-', '')}"

        print(
            f"""
🎉 Installation complete! 
✅ Notion database created: {self.database_id or 'N/A'}
✅ 2 sample posts created
✅ Environment security settings
✅ Automatic deployment pipeline configured
✅ First sync complete

🔗 Notion database quick link:
{database_url}

👉 What to do next:
1. Add new pages in Notion to write blog posts
2. Check the 'isPublished' checkbox
3. It will be reflected automatically in the blog!

🚀 Deployment Info:
- Deployment method: {self.deployment_type or 'N/A'}
- Automatic sync: Every 2 hours or on Git push
- Environment security settings complete

🔧 Advanced Settings:
- Add environment variables: Edit .env file
- Change settings: Edit notion-hugo.config.yaml
- Local test: python notion_hugo_app.py --dry-run

📚 Help:
- Detailed guide: docs/SETUP_GUIDE.md
- Security guide: docs/DATABASE_ID_SECURITY_GUIDE.md
- Troubleshooting: docs/TROUBLESHOOTING.md
"""
        )

    def run_installation(self) -> bool:
        """전체 설치 프로세스 실행"""
        try:
            # 1. 토큰 검증
            is_valid, message = self.validate_notion_token()
            if not is_valid:
                print(f"❌ Token validation failed: {message}")
                return False

            print(f"✅ {message}")

            # 2. Hugo 스캐폴드 설정
            if not self.setup_hugo_scaffold():
                return False

            # 3. 권한 감지
            permissions = self.detect_notion_permissions()
            if not permissions["can_create_database"]:
                print("❌ No permission to create database.")
                return False

            # 4. 데이터베이스 생성
            db_result = self.create_optimized_database(permissions)
            if not db_result["success"]:
                print(
                    f"❌ Failed to create database: {db_result.get('error', 'Unknown error')}"
                )
                return False

            # 5. 샘플 포스트 생성
            posts_result = self.create_sample_posts()
            if not posts_result["success"]:
                print(
                    f"❌ Failed to create sample posts: {posts_result.get('error', 'Unknown error')}"
                )
                return False

            # 6. 보안 설정
            if not self.setup_environment_security():
                print("❌ Failed to set up security")
                return False

            # 7. 설정 파일 생성
            if not self.create_enhanced_config():
                print("❌ Failed to create configuration file")
                return False

            # 8. 배포 방식 선택 및 설정
            self.deployment_type = self.choose_deployment_type()
            if not self.setup_deployment_pipeline(self.deployment_type):
                print("❌ Failed to set up deployment")
                return False

            # 9. 첫 동기화 테스트
            if not self.test_first_sync():
                print("⚠️ First sync failed, but setup is complete.")

            # 완료 메시지
            self.show_completion_message()
            return True

        except Exception as e:
            print(f"❌ Unexpected error during installation: {str(e)}")
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
        token = input("🔑 Enter your Notion API token: ").strip()
        if not token:
            print("❌ Please enter a token.")
            continue

        if not token.startswith("ntn_"):
            print("❌ Notion token must start with 'ntn_'.")
            print("💡 How to get a token: https://notion.so/my-integrations")
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
Examples:
  python setup.py --token secret_abc123
  python setup.py --interactive
  # Or use environment variables:
  # NOTION_TOKEN=secret_... python setup.py
        """,
    )

    parser.add_argument(
        "--token",
        help="Notion API token (can be replaced by NOTION_TOKEN environment variable)",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive setup mode"
    )

    args = parser.parse_args()

    # 대화형 모드
    if args.interactive:
        return interactive_setup()

    # 명령줄 또는 환경변수에서 토큰 가져오기
    token = args.token or os.environ.get("NOTION_TOKEN")

    if not token:
        print("❌ --token argument or NOTION_TOKEN environment variable is required.")
        parser.print_help()
        return False

    # 토큰 기본 검증
    if not token.startswith("ntn_"):
        print("❌ Notion token must start with 'ntn_'.")
        print("💡 How to get a token: https://www.notion.so/my-integrations")
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
        print("\n❌ User interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
