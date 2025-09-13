#!/usr/bin/env python3
"""
Hugo Setup and Initialization Utilities

This module provides utilities for automatically setting up Hugo sites,
including directory creation, theme submodule setup, and configuration generation.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from ..config import ConfigManager
    from ..cli_utils import print_info, print_success, print_error, print_warning
except ImportError:
    try:
        from .config import ConfigManager
        from .cli_utils import print_info, print_success, print_error, print_warning
    except ImportError:
        from config import ConfigManager
        from cli_utils import print_info, print_success, print_error, print_warning


class HugoSetup:
    """Hugo site setup and initialization manager."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize Hugo setup manager.

        Args:
            config_manager: Optional ConfigManager instance. If None, creates a new one.
        """
        self.config_manager = config_manager or ConfigManager()
        self.project_root = Path.cwd()

    def ensure_hugo_installed(self) -> bool:
        """Check if Hugo is installed and available.

        Returns:
            True if Hugo is installed, False otherwise.
        """
        try:
            result = subprocess.run(
                ["hugo", "version"], capture_output=True, text=True, check=True
            )
            print_success(f"✅ Hugo is installed: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("⚠️ Hugo is not installed or not in PATH")
            print_info("📥 Please install Hugo from: https://gohugo.io/installation/")
            return False

    def create_hugo_site_structure(self, hugo_root: str = "site") -> bool:
        """Create Hugo site structure if it doesn't exist.

        Args:
            hugo_root: Root directory for Hugo site (default: "site")

        Returns:
            True if structure was created successfully, False otherwise.
        """
        hugo_path = self.project_root / hugo_root

        # If Hugo site already exists, skip creation
        if (
            (hugo_path / "config").exists()
            or (hugo_path / "config.yaml").exists()
            or (hugo_path / "config.toml").exists()
        ):
            print_info(f"📁 Hugo site already exists at: {hugo_path}")
            return True

        try:
            # Create Hugo site structure
            if not hugo_path.exists():
                print_info(f"🏗️ Creating Hugo site structure at: {hugo_path}")

                # Use hugo new site if Hugo is installed
                if self.ensure_hugo_installed():
                    subprocess.run(
                        ["hugo", "new", "site", hugo_root, "--force"],
                        cwd=self.project_root,
                        check=True,
                    )
                    print_success(f"✅ Hugo site created with 'hugo new site'")
                else:
                    # Manual creation if Hugo is not available
                    self._create_manual_hugo_structure(hugo_path)
                    print_success(f"✅ Hugo site structure created manually")

            return True

        except subprocess.CalledProcessError as e:
            print_error(f"❌ Failed to create Hugo site: {e}")
            return False
        except Exception as e:
            print_error(f"❌ Unexpected error creating Hugo site: {e}")
            return False

    def _create_manual_hugo_structure(self, hugo_path: Path) -> None:
        """Create Hugo directory structure manually.

        Args:
            hugo_path: Path to Hugo site root
        """
        directories = [
            "archetypes",
            "content/posts",
            "content/pages",
            "data",
            "layouts",
            "static",
            "themes",
            "config/_default",
        ]

        for directory in directories:
            dir_path = hugo_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create basic archetype
        archetype_content = """---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
---

"""
        (hugo_path / "archetypes" / "default.md").write_text(archetype_content)

        # Create basic config
        config_content = """baseURL: 'https://example.org'
languageCode: 'en-us'
title: 'My New Hugo Site'
"""
        (hugo_path / "config.yaml").write_text(config_content)

    def setup_theme_submodule(
        self, hugo_root: str = "site", theme_name: str = "PaperMod"
    ) -> bool:
        """Setup Hugo theme as git submodule.

        Args:
            hugo_root: Root directory for Hugo site
            theme_name: Theme name (default: "PaperMod")

        Returns:
            True if theme was setup successfully, False otherwise.
        """
        theme_path = self.project_root / hugo_root / "themes" / theme_name

        # If theme already exists, skip setup
        if theme_path.exists() and (theme_path / ".git").exists():
            print_info(f"🎨 Theme '{theme_name}' already exists at: {theme_path}")
            return True

        try:
            # Remove existing theme directory if it exists but is not a git repo
            if theme_path.exists():
                shutil.rmtree(theme_path)

            # Theme URLs mapping
            theme_urls = {
                "PaperMod": "https://github.com/adityatelange/hugo-PaperMod.git",
                "Ananke": "https://github.com/theNewDynamic/gohugo-theme-ananke.git",
                "Terminal": "https://github.com/panr/hugo-theme-terminal.git",
            }

            theme_url = theme_urls.get(theme_name, theme_urls["PaperMod"])
            submodule_path = f"{hugo_root}/themes/{theme_name}"

            print_info(f"🎨 Adding theme '{theme_name}' as git submodule...")

            # Add git submodule
            subprocess.run(
                ["git", "submodule", "add", theme_url, submodule_path],
                cwd=self.project_root,
                check=True,
            )

            # Initialize and update submodule
            subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                cwd=self.project_root,
                check=True,
            )

            print_success(f"✅ Theme '{theme_name}' added as git submodule")

            # Update .gitmodules if needed
            self.config_manager.create_gitmodules_file()

            return True

        except subprocess.CalledProcessError as e:
            print_error(f"❌ Failed to setup theme submodule: {e}")
            return False
        except Exception as e:
            print_error(f"❌ Unexpected error setting up theme: {e}")
            return False

    def create_hugo_config(self, hugo_root: str = "site") -> bool:
        """Create Hugo configuration files from notion-hugo config.

        Args:
            hugo_root: Root directory for Hugo site

        Returns:
            True if config was created successfully, False otherwise.
        """
        try:
            config = self.config_manager.load_config()
            hugo_config = config.get("hugo", {})
            site_config = hugo_config.get("site", {})
            theme_config = hugo_config.get("theme", {})

            # Build Hugo config.yaml
            hugo_config_data = {
                "baseURL": site_config.get("base_url", "https://example.org"),
                "languageCode": site_config.get("language", "en"),
                "title": site_config.get("title", "My Hugo Site"),
                "theme": theme_config.get("name", "PaperMod"),
                "params": theme_config.get("params", {}),
                "menu": hugo_config.get("menu", {}),
                "markup": hugo_config.get("content", {}).get("markdown", {}),
                "permalinks": hugo_config.get("urls", {}).get("permalinks", {}),
            }

            # Write config file
            config_path = self.project_root / hugo_root / "config.yaml"

            import yaml

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    hugo_config_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            print_success(f"✅ Hugo config created: {config_path}")
            return True

        except Exception as e:
            print_error(f"❌ Failed to create Hugo config: {e}")
            return False

    def full_hugo_setup(self) -> bool:
        """Perform complete Hugo setup: structure + theme + config.

        Returns:
            True if setup was successful, False otherwise.
        """
        print_info("🚀 Starting complete Hugo setup...")

        # Get Hugo root from config
        hugo_root = self.config_manager.get_hugo_root_path()

        # Step 1: Create Hugo site structure
        if not self.create_hugo_site_structure(hugo_root):
            return False

        # Step 2: Setup theme submodule
        config = self.config_manager.load_config()
        theme_name = config.get("hugo", {}).get("theme", {}).get("name", "PaperMod")

        if not self.setup_theme_submodule(hugo_root, theme_name):
            print_warning("⚠️ Theme setup failed, continuing without theme...")

        # Step 3: Create Hugo configuration
        if not self.create_hugo_config(hugo_root):
            return False

        print_success("🎉 Complete Hugo setup finished successfully!")
        print_info(f"📁 Hugo site location: {self.project_root / hugo_root}")
        print_info(f"🎨 Theme: {theme_name}")
        print_info("🚀 Next steps:")
        print_info(f"   cd {hugo_root}")
        print_info("   hugo server")

        return True


def ensure_hugo_setup(config_manager: Optional[ConfigManager] = None) -> bool:
    """Convenience function to ensure Hugo setup is complete.

    Args:
        config_manager: Optional ConfigManager instance

    Returns:
        True if Hugo setup is ready, False otherwise.
    """
    setup = HugoSetup(config_manager)

    hugo_root = setup.config_manager.get_hugo_root_path()
    hugo_path = Path.cwd() / hugo_root

    # Check if Hugo site exists and is properly configured
    if (
        hugo_path.exists()
        and (hugo_path / "content").exists()
        and (hugo_path / "themes").exists()
        and (
            (hugo_path / "config.yaml").exists()
            or (hugo_path / "config.toml").exists()
            or (hugo_path / "config").exists()
        )
    ):
        print_info(f"✅ Hugo site is already set up at: {hugo_path}")
        return True
    else:
        print_info("🏗️ Hugo site not found, setting up automatically...")
        return setup.full_hugo_setup()


class BuildManager:
    """
    Stage 4: hugo/ → hugo/public/
    
    Build static site using Hugo.
    """
    
    def __init__(self, source_dir: str = "hugo", output_dir: str = "hugo/public", 
                 minify: bool = False, base_url: Optional[str] = None):
        """
        Initialize BuildManager.
        
        Args:
            source_dir: Hugo source directory
            output_dir: Build output directory 
            minify: Whether to minify output
            base_url: Base URL for the site
        """
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.minify = minify
        self.base_url = base_url
        self.file_count = 0
        self.errors = []
        
    def run(self) -> dict:
        """
        Execute Stage 4 build.
        
        Returns:
            Dictionary with build results
        """
        try:
            print(f"[Info] BuildManager: {self.source_dir}/ → {self.output_dir}/")
            
            # Ensure output directory exists
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Build Hugo command
            cmd = ["hugo"]
            
            if self.minify:
                cmd.append("--minify")
            
            if self.base_url:
                cmd.extend(["--baseURL", self.base_url])
            
            # Set destination
            cmd.extend(["--destination", self.output_dir])
            
            # Run Hugo build
            print(f"[Info] Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.source_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Count output files
                output_path = Path(self.output_dir)
                if output_path.exists():
                    files = list(output_path.rglob("*"))
                    self.file_count = len([f for f in files if f.is_file()])
                
                print(f"[Info] Build successful: {self.file_count} files generated")
                return {
                    "success": True,
                    "file_count": self.file_count,
                    "source_dir": self.source_dir,
                    "output_dir": self.output_dir,
                    "build_output": result.stdout
                }
            else:
                error_msg = f"Hugo build failed: {result.stderr or result.stdout}"
                print(f"[Error] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "file_count": 0,
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Hugo build timed out after 5 minutes"
            print(f"[Error] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_count": 0
            }
        except Exception as e:
            error_msg = f"Build failed with exception: {str(e)}"
            print(f"[Error] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_count": 0
            }


if __name__ == "__main__":
    # Test Hugo setup
    setup = HugoSetup()
    success = setup.full_hugo_setup()
    sys.exit(0 if success else 1)
