#!/usr/bin/env python3
"""
Smart Configuration Manager for Notion-Hugo
Automatically detects deployment environment and applies optimal settings
"""

import os
import yaml
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
try:
    from ..cli_utils import print_info, print_success, print_error, print_warning
except ImportError:
    # Fallback print functions when cli_utils not available
    def print_info(msg): print(f"ℹ️  {msg}")
    def print_success(msg): print(f"✅ {msg}")
    def print_error(msg): print(f"❌ {msg}")
    def print_warning(msg): print(f"⚠️  {msg}")


class SmartConfigManager:
    """Automatically detects deployment environment and applies optimal configuration"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.environment = self.detect_environment()
        self.github_info = self.get_github_info()

    def detect_environment(self) -> str:
        """Automatically detect deployment environment"""
        if os.environ.get("GITHUB_ACTIONS"):
            return "github_actions"
        elif os.environ.get("VERCEL"):
            return "vercel"
        elif os.environ.get("NETLIFY"):
            return "netlify"
        elif os.environ.get("CI"):
            return "ci"
        else:
            return "local"

    def get_github_info(self) -> Dict[str, str]:
        """Extract GitHub repository information"""
        info = {"owner": "", "repo": "", "default_branch": "main"}

        # From GitHub Actions environment
        if os.environ.get("GITHUB_REPOSITORY"):
            repo = os.environ.get("GITHUB_REPOSITORY", "")
            if "/" in repo:
                owner, repo_name = repo.split("/")
                info["owner"] = owner
                info["repo"] = repo_name
            info["default_branch"] = os.environ.get("GITHUB_REF_NAME", "main")
            return info

        # From local git repository
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL
                if "github.com" in url:
                    # SSH format: git@github.com:owner/repo.git
                    if url.startswith("git@"):
                        parts = url.split(":")[1].replace(".git", "").split("/")
                    # HTTPS format: https://github.com/owner/repo.git
                    else:
                        parts = (
                            url.replace("https://github.com/", "")
                            .replace(".git", "")
                            .split("/")
                        )

                    if len(parts) >= 2:
                        info["owner"] = parts[0]
                        info["repo"] = parts[1]

            # Get default branch
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                info["default_branch"] = result.stdout.strip().split("/")[-1]
        except Exception:
            pass

        return info

    def get_base_url(self, deployment_target: str = "github") -> str:
        """Automatically set base URL according to environment"""

        # Check explicit setting from environment variables
        if os.environ.get("HUGO_BASE_URL"):
            return os.environ.get("HUGO_BASE_URL")

        if deployment_target == "github" or self.environment == "github_actions":
            # GitHub Pages URL pattern
            if self.github_info["owner"] and self.github_info["repo"]:
                owner = self.github_info["owner"]
                repo = self.github_info["repo"]

                # For username.github.io format
                if repo.endswith(".github.io"):
                    return f"https://{repo}"
                # For general project case
                else:
                    return f"https://{owner}.github.io/{repo}"

        elif deployment_target == "vercel" or self.environment == "vercel":
            # Vercel automatic URL detection
            vercel_url = os.environ.get("VERCEL_URL")
            if vercel_url:
                return f"https://{vercel_url}"
            # Custom domain
            custom_domain = os.environ.get("CUSTOM_DOMAIN")
            if custom_domain:
                return f"https://{custom_domain}"

        # Local or default value
        return "http://localhost:1313"

    def generate_hugo_config(self, deployment_target: str = "github") -> Dict[str, Any]:
        """Automatically generate Hugo configuration by environment"""
        base_url = self.get_base_url(deployment_target)

        config = {
            "baseURL": base_url,
            "languageCode": "ko-kr",
            "title": os.environ.get("SITE_TITLE", "My Notion Blog"),
            "theme": "PaperMod",
            "paginate": 10,
            "enableRobotsTXT": True,
            "buildDrafts": False,
            "buildFuture": False,
            "buildExpired": False,
            "enableGitInfo": True,
            "googleAnalytics": os.environ.get("GA_ID", ""),
            # GitHub Pages optimization
            "canonifyURLs": False,  # False is recommended for GitHub Pages
            "relativeURLs": False,
            "taxonomies": {"category": "categories", "tag": "tags", "series": "series"},
            "permalinks": {"posts": "/:year/:month/:slug/", "pages": "/:slug/"},
            "outputs": {"home": ["HTML", "RSS", "JSON"]},
            "params": self.get_theme_params(deployment_target),
            "menu": {
                "main": [
                    {"name": "Posts", "url": "/posts/", "weight": 5},
                    {"name": "Tags", "url": "/tags/", "weight": 10},
                    {"name": "Categories", "url": "/categories/", "weight": 15},
                    {"name": "Search", "url": "/search/", "weight": 20},
                ]
            },
            "markup": {
                "goldmark": {"renderer": {"unsafe": True}},
                "highlight": {
                    "codeFences": True,
                    "guessSyntax": True,
                    "lineNos": False,
                    "style": "monokai",
                },
            },
        }

        # GitHub Pages special settings
        if deployment_target == "github":
            # For subdirectory deployment
            if not base_url.endswith(".github.io"):
                repo_name = self.github_info.get("repo", "")
                if repo_name and not repo_name.endswith(".github.io"):
                    # Project pages need subdirectory path
                    config["canonifyURLs"] = True

        # Vercel special settings
        elif deployment_target == "vercel":
            config["relativeURLs"] = False
            config["canonifyURLs"] = True

        return config

    def get_theme_params(self, deployment_target: str = "github") -> Dict[str, Any]:
        """Configure PaperMod theme parameters"""
        params = {
            # Basic settings
            "env": "production",
            "title": os.environ.get("SITE_TITLE", "My Notion Blog"),
            "description": os.environ.get(
                "SITE_DESCRIPTION", "A blog powered by Notion and Hugo"
            ),
            "keywords": ["blog", "notion", "hugo"],
            "author": os.environ.get("SITE_AUTHOR", "Me"),
            "DateFormat": "January 2, 2006",
            "defaultTheme": "auto",
            "disableThemeToggle": False,
            # Feature settings
            "ShowReadingTime": True,
            "ShowShareButtons": True,
            "ShowPostNavLinks": True,
            "ShowBreadCrumbs": True,
            "ShowCodeCopyButtons": True,
            "ShowWordCount": True,
            "ShowRssButtonInSectionTermList": True,
            "UseHugoToc": True,
            "disableSpecial1stPost": False,
            "disableScrollToTop": False,
            "comments": False,
            "hidemeta": False,
            "hideSummary": False,
            "showtoc": True,
            "tocopen": False,
            # Home information
            "homeInfoParams": {
                "Title": "Hi there 👋",
                "Content": "Welcome to my blog powered by Notion and Hugo",
            },
            # Social icons
            "socialIcons": [
                {
                    "name": "github",
                    "url": f"https://github.com/{self.github_info.get('owner', '')}",
                },
                {"name": "rss", "url": "/index.xml"},
            ],
            # Search
            "fuseOpts": {
                "isCaseSensitive": False,
                "shouldSort": True,
                "location": 0,
                "distance": 1000,
                "threshold": 0.4,
                "minMatchCharLength": 0,
                "keys": ["title", "permalink", "summary", "content"],
            },
        }

        # Additional settings by environment
        if deployment_target == "vercel":
            params["images"] = ["/og-image.png"]
            params["vercel"] = True

        return params

    def create_hugo_config_file(
        self, deployment_target: str = "github", config_path: str = None
    ) -> bool:
        """Create/update Hugo configuration file"""
        if config_path is None:
            config_path = self.project_root / "hugo.yaml"
        else:
            config_path = Path(config_path)

        try:
            # Create backup
            if config_path.exists():
                backup_path = config_path.with_suffix(
                    f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                )
                shutil.copy(config_path, backup_path)
                print_info(f"📦 Created backup: {backup_path}")

            # Create new configuration
            config = self.generate_hugo_config(deployment_target)

            # Save as YAML
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            print_success(f"✅ Hugo configuration created: {config_path}")
            print_info(f"🔗 Base URL: {config['baseURL']}")

            return True

        except Exception as e:
            print_error(f"Failed to create Hugo config: {str(e)}")
            return False

    def validate_github_pages_setup(self) -> Tuple[bool, List[str]]:
        """Validate GitHub Pages setup"""
        issues = []

        # 1. Check GitHub information
        if not self.github_info.get("owner") or not self.github_info.get("repo"):
            issues.append(
                "GitHub repository information not found. Please ensure you're in a git repository."
            )

        # 2. Check GitHub Actions workflow
        workflow_path = (
            self.project_root / ".github" / "workflows" / "notion-hugo-deploy.yml"
        )
        if not workflow_path.exists():
            issues.append(f"GitHub Actions workflow not found at {workflow_path}")

        # 3. Check required environment variables
        required_env = ["NOTION_TOKEN"]
        for env in required_env:
            if not os.environ.get(env):
                issues.append(f"Environment variable {env} not set")

        # 4. Check Hugo theme
        theme_path = self.project_root / "themes" / "PaperMod"
        if not theme_path.exists():
            issues.append("PaperMod theme not installed")

        # 5. Check config file
        config_files = ["hugo.yaml", "hugo.toml", "config.yaml", "config.toml"]
        config_exists = any((self.project_root / f).exists() for f in config_files)
        if not config_exists:
            issues.append("Hugo configuration file not found")

        return len(issues) == 0, issues

    def setup_github_pages(self) -> bool:
        """Complete GitHub Pages setup"""
        print_info("🚀 Setting up GitHub Pages deployment")

        # 1. Check GitHub information
        if not self.github_info.get("owner"):
            print_error(
                "Not a GitHub repository. Please initialize git and add remote origin first."
            )
            return False

        print_info(
            f"📍 Repository: {self.github_info['owner']}/{self.github_info['repo']}"
        )

        # 2. Create Hugo configuration
        print_info("📝 Creating Hugo configuration...")
        if not self.create_hugo_config_file("github"):
            return False

        # 3. Create GitHub Actions workflow
        print_info("⚙️ Creating GitHub Actions workflow...")
        if not self.create_github_workflow():
            return False

        # 4. Validation
        valid, issues = self.validate_github_pages_setup()
        if valid:
            print_success("✅ GitHub Pages setup complete!")
            print_info("📌 Next steps:")
            print_info("  1. Set NOTION_TOKEN secret in GitHub repository settings")
            print_info("  2. Push changes to trigger deployment")
            print_info(
                f"  3. Your site will be available at: {self.get_base_url('github')}"
            )
        else:
            print_warning("⚠️ Setup completed with issues:")
            for issue in issues:
                print_warning(f"  - {issue}")

        return valid

    def create_github_workflow(self) -> bool:
        """Create GitHub Actions workflow"""
        workflow_dir = self.project_root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_path = workflow_dir / "notion-hugo-deploy.yml"

        # Skip if already exists
        if workflow_path.exists():
            print_info("GitHub Actions workflow already exists")
            return True

        workflow_content = self.generate_github_workflow()

        try:
            with open(workflow_path, "w", encoding="utf-8") as f:
                f.write(workflow_content)
            print_success(f"✅ Created workflow: {workflow_path}")
            return True
        except Exception as e:
            print_error(f"Failed to create workflow: {str(e)}")
            return False

    def generate_github_workflow(self) -> str:
        """Generate GitHub Actions workflow"""
        return """name: Notion → Hugo → GitHub Pages

on:
  push:
    branches: ["main"]
  schedule:
    - cron: '0 */2 * * *'  # Run every 2 hours
  workflow_dispatch:
    inputs:
      sync_mode:
        description: 'Sync mode'
        required: false
        default: 'incremental'
        type: choice
        options:
        - incremental
        - full-sync

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

env:
  HUGO_VERSION: 0.128.0

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        run: |
          wget -O ${{ runner.temp }}/hugo.deb \\
            https://github.com/gohugoio/hugo/releases/download/v${{ env.HUGO_VERSION }}/hugo_extended_${{ env.HUGO_VERSION }}_linux-amd64.deb
          sudo dpkg -i ${{ runner.temp }}/hugo.deb

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r dev/requirements.txt

      - name: Sync from Notion
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
        run: |
          python app.py sync --mode ${{ github.event.inputs.sync_mode || 'incremental' }}

      - name: Build with Hugo
        run: |
          hugo --minify

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


class ThemeManager:
    """Automatic Hugo theme management"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.themes_dir = self.project_root / "themes"

    def ensure_papermod_theme(self) -> bool:
        """Check and install PaperMod theme"""
        theme_path = self.themes_dir / "PaperMod"

        if theme_path.exists():
            print_info("✅ PaperMod theme already installed")
            return True

        print_info("📦 Installing PaperMod theme...")
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Add as Git submodule
            subprocess.run(
                [
                    "git",
                    "submodule",
                    "add",
                    "-f",
                    "https://github.com/adityatelange/hugo-PaperMod.git",
                    "themes/PaperMod",
                ],
                check=True,
                cwd=self.project_root,
            )

            # Initialize submodule
            subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                check=True,
                cwd=self.project_root,
            )

            print_success("✅ PaperMod theme installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install theme: {str(e)}")
            print_info("Try manual installation:")
            print_info(
                "  git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod"
            )
            return False
