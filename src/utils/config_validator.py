#!/usr/bin/env python3
"""
Configuration validator for Notion-Hugo
Ensures all settings are correct before deployment
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .cli_utils import print_info, print_success, print_error, print_warning


class ConfigValidator:
    """Validate and fix configuration issues"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.issues = []
        self.fixes_applied = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks
        Returns: (is_valid, issues, fixes_applied)
        """
        self.issues = []
        self.fixes_applied = []

        # Check environment variables
        self._check_env_vars()

        # Check configuration files
        self._check_config_files()

        # Check Hugo setup
        self._check_hugo_setup()

        # Check Notion setup
        self._check_notion_setup()

        # Check Git/GitHub setup
        self._check_github_setup()

        is_valid = len(self.issues) == 0
        return is_valid, self.issues, self.fixes_applied

    def _check_env_vars(self):
        """Check required environment variables"""
        required = {"NOTION_TOKEN": "Notion API token for accessing your workspace"}

        optional = {
            "NOTION_DATABASE_ID_POSTS": "Database ID for blog posts",
            "HUGO_BASE_URL": "Override base URL for Hugo",
            "GA_ID": "Google Analytics tracking ID",
        }

        # Check required
        for var, description in required.items():
            if not os.environ.get(var):
                self.issues.append(f"Missing required env var: {var} ({description})")

                # Try to load from .env
                env_file = self.project_root / ".env"
                if env_file.exists():
                    from dotenv import load_dotenv

                    load_dotenv(env_file)
                    if os.environ.get(var):
                        self.fixes_applied.append(f"Loaded {var} from .env file")
                    else:
                        self.issues.append(f"  → Add to .env: {var}=your_value_here")

        # Check optional
        for var, description in optional.items():
            if not os.environ.get(var):
                print_info(f"Optional env var not set: {var} ({description})")

    def _check_config_files(self):
        """Check configuration files"""
        configs_to_check = [
            ("hugo.yaml", self._validate_hugo_config),
            ("config.yaml", self._validate_hugo_config),
            ("src/config/notion-hugo-config.yaml", self._validate_notion_config),
            (".env", self._validate_env_file),
        ]

        for filename, validator in configs_to_check:
            filepath = self.project_root / filename
            if filepath.exists():
                try:
                    validator(filepath)
                except Exception as e:
                    self.issues.append(f"Invalid {filename}: {str(e)}")
            elif filename in ["hugo.yaml", "config.yaml"]:
                # At least one Hugo config must exist
                pass
            elif filename == "src/config/notion-hugo-config.yaml":
                self.issues.append(
                    f"Missing {filename} - run 'python app.py quickstart'"
                )

    def _validate_hugo_config(self, filepath: Path):
        """Validate Hugo configuration"""
        with open(filepath, "r") as f:
            config = yaml.safe_load(f)

        required_fields = ["baseURL", "title", "theme"]
        for field in required_fields:
            if field not in config:
                self.issues.append(f"Hugo config missing required field: {field}")

                # Auto-fix some fields
                if field == "theme":
                    config["theme"] = "PaperMod"
                    self.fixes_applied.append("Set theme to PaperMod")
                elif field == "baseURL":
                    config["baseURL"] = "http://localhost:1313"
                    self.fixes_applied.append("Set baseURL to localhost")
                elif field == "title":
                    config["title"] = "My Blog"
                    self.fixes_applied.append("Set default title")

        # Check theme exists
        if "theme" in config:
            theme_path = self.project_root / "themes" / config["theme"]
            if not theme_path.exists():
                self.issues.append(
                    f"Theme '{config['theme']}' not installed at {theme_path}"
                )

    def _validate_notion_config(self, filepath: Path):
        """Validate Notion configuration"""
        with open(filepath, "r") as f:
            config = yaml.safe_load(f)

        if "notion" not in config:
            self.issues.append(
                "src/config/notion-hugo-config.yaml missing 'notion' section"
            )
            return

        notion_config = config["notion"]

        # Check mount configuration
        if "mount" not in notion_config:
            self.issues.append("Notion config missing 'mount' section")
            return

        mount = notion_config["mount"]

        # Check databases
        if "databases" not in mount or not mount["databases"]:
            self.issues.append(
                "No databases configured in src/config/notion-hugo-config.yaml"
            )
        else:
            for db in mount["databases"]:
                if "database_id" not in db:
                    self.issues.append("Database configuration missing 'database_id'")
                if "target_folder" not in db:
                    self.issues.append("Database configuration missing 'target_folder'")

    def _validate_env_file(self, filepath: Path):
        """Validate .env file"""
        with open(filepath, "r") as f:
            lines = f.readlines()

        has_notion_token = any("NOTION_TOKEN" in line for line in lines)
        if not has_notion_token:
            self.issues.append(".env file exists but missing NOTION_TOKEN")

    def _check_hugo_setup(self):
        """Check Hugo installation and setup"""
        # Check if Hugo is installed
        import subprocess

        try:
            result = subprocess.run(
                ["hugo", "version"], capture_output=True, text=True, check=True
            )
            version_output = result.stdout
            print_info(f"Hugo installed: {version_output.split()[0]}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.issues.append("Hugo not installed - install from https://gohugo.io")

        # Check content directory
        content_dir = self.project_root / "content"
        if not content_dir.exists():
            content_dir.mkdir(parents=True, exist_ok=True)
            self.fixes_applied.append("Created content directory")

        # Check if there's at least one post
        posts_dir = content_dir / "posts"
        if posts_dir.exists():
            md_files = list(posts_dir.glob("*.md"))
            if not md_files:
                print_warning("No posts found in blog/content/posts/")

    def _check_notion_setup(self):
        """Check Notion API setup"""
        if not os.environ.get("NOTION_TOKEN"):
            return  # Already checked in env vars

        # Try to connect to Notion
        try:
            from notion_client import Client

            notion = Client(
                auth=os.environ.get("NOTION_TOKEN"),
                notion_version="2025-09-03"
            )

            # Try to get user info
            user = notion.users.me()
            print_info(f"Notion connected as: {user.get('name', 'Unknown')}")

        except Exception as e:
            self.issues.append(f"Cannot connect to Notion API: {str(e)}")

    def _check_github_setup(self):
        """Check GitHub repository setup"""
        import subprocess

        try:
            # Check if it's a git repo
            subprocess.run(
                ["git", "status"],
                capture_output=True,
                check=True,
                cwd=self.project_root,
            )

            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )

            remote_url = result.stdout.strip()
            if "github.com" in remote_url:
                print_info(f"GitHub remote: {remote_url}")
            else:
                print_warning("Remote origin is not GitHub")

        except subprocess.CalledProcessError:
            print_warning("Not a git repository or no remote configured")
            print_info(
                "Initialize with: git init && git remote add origin YOUR_GITHUB_URL"
            )

    def auto_fix(self) -> int:
        """
        Attempt to auto-fix common issues
        Returns number of fixes applied
        """
        fixes = 0

        # Create missing directories
        dirs_to_create = ["blog/content/posts", "blog/themes", "blog/static", "blog/layouts"]

        for dir_name in dirs_to_create:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append(f"Created directory: {dir_name}")
                fixes += 1

        # Create .env template if missing
        env_file = self.project_root / ".env"
        if not env_file.exists():
            template = """# Notion-Hugo Configuration
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID_POSTS=your_database_id_here

# Optional
HUGO_BASE_URL=
GA_ID=
SITE_TITLE=My Blog
SITE_AUTHOR=Your Name
"""
            with open(env_file, "w") as f:
                f.write(template)
            self.fixes_applied.append("Created .env template")
            fixes += 1

        return fixes


def run_validation_check(auto_fix: bool = False) -> bool:
    """
    Run configuration validation

    Args:
        auto_fix: Whether to attempt auto-fixes

    Returns:
        True if valid, False otherwise
    """
    validator = ConfigValidator()

    print_info("🔍 Running configuration validation...")

    is_valid, issues, fixes = validator.validate_all()

    if fixes:
        print_info("\n🔧 Auto-fixes applied:")
        for fix in fixes:
            print_success(f"  ✅ {fix}")

    if auto_fix and issues:
        print_info("\n🔧 Attempting additional auto-fixes...")
        fixed_count = validator.auto_fix()
        if fixed_count > 0:
            print_success(f"Applied {fixed_count} additional fixes")

            # Re-validate
            is_valid, issues, _ = validator.validate_all()

    if issues:
        print_error("\n❌ Validation issues found:")
        for issue in issues:
            print_warning(f"  • {issue}")
        return False
    else:
        print_success("\n✅ All validation checks passed!")
        return True
