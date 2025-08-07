#!/usr/bin/env python3
"""
Unified Configuration Management System for Notion-Hugo Integration.

This module provides a comprehensive configuration management system that:
1. Uses unified config.yaml structure with hierarchical sections
2. Supports environment variable overrides with SECTION_SUBSECTION_KEY pattern
3. Maintains backward compatibility with existing configuration usage
4. Implements proper type hints and error handling
5. Provides validation and auto-recovery features

Example usage:
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Environment variable NOTION_API_TOKEN overrides notion.api.token
    # Environment variable HUGO_SITE_TITLE overrides hugo.site.title
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, TypedDict, Any, Union, Tuple
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError


# Type definitions for the unified configuration structure
class NotionApiConfig(TypedDict):
    token: str
    timeout: int
    retry: Dict[str, Any]


class NotionMountConfig(TypedDict):
    auto_discovery: Dict[str, Any]
    databases: List[Dict[str, Any]]
    pages: List[Dict[str, Any]]


class NotionSyncConfig(TypedDict):
    mode: str
    batch_size: int
    include_drafts: bool
    filters: Dict[str, Any]


class NotionConfig(TypedDict):
    api: NotionApiConfig
    mount: NotionMountConfig
    sync: NotionSyncConfig


class HugoSiteConfig(TypedDict):
    base_url: str
    title: str
    description: str
    language: str
    author: str


class HugoThemeConfig(TypedDict):
    name: str
    params: Dict[str, Any]


class HugoContentConfig(TypedDict):
    markdown: Dict[str, Any]
    highlight: Dict[str, Any]
    math: Dict[str, Any]


class HugoConfig(TypedDict):
    site: HugoSiteConfig
    theme: HugoThemeConfig
    content: HugoContentConfig
    menu: Dict[str, Any]
    seo: Dict[str, Any]
    urls: Dict[str, Any]


class ContentConfig(TypedDict):
    images: Dict[str, Any]
    files: Dict[str, Any]
    validation: Dict[str, Any]


class DeploymentConfig(TypedDict):
    strategy: str
    github_actions: Dict[str, Any]
    schedule: Dict[str, Any]
    build: Dict[str, Any]


class DevelopmentConfig(TypedDict):
    server: Dict[str, Any]
    debug: Dict[str, Any]
    docker: Dict[str, Any]


class SecurityConfig(TypedDict):
    environment_variables: Dict[str, Any]
    logging: Dict[str, Any]
    data: Dict[str, Any]


class FeaturesConfig(TypedDict):
    experimental: Dict[str, Any]
    legacy: Dict[str, Any]


class MetadataConfig(TypedDict):
    config_version: str
    generated_at: str
    generated_by: str
    last_updated: str
    compatibility: Dict[str, Any]


class UnifiedConfig(TypedDict):
    """Unified configuration structure for Notion-Hugo integration."""

    notion: NotionConfig
    hugo: HugoConfig
    content: ContentConfig
    deployment: DeploymentConfig
    development: DevelopmentConfig
    security: SecurityConfig
    features: FeaturesConfig
    metadata: MetadataConfig


# Legacy type definitions for backward compatibility
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


class LegacyDeploymentConfig(TypedDict):
    auto_deploy: bool
    trigger: str
    schedule: Optional[str]
    environment: str


class LegacySecurityConfig(TypedDict):
    use_environment_variables: bool
    mask_sensitive_logs: bool
    token_validation: bool


class LegacyConfig(TypedDict):
    """Legacy configuration structure for backward compatibility."""

    mount: Mount
    filename: Optional[FilenameConfig]
    deployment: Optional[LegacyDeploymentConfig]
    security: Optional[LegacySecurityConfig]


# Union type for configuration (supports both unified and legacy)
Config = Union[UnifiedConfig, LegacyConfig]


class ConfigManager:
    """Unified Configuration Manager for Notion-Hugo Integration.

    This class manages configuration loading from the unified config.yaml file
    with support for environment variable overrides using the SECTION_SUBSECTION_KEY pattern.

    Example:
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # Access unified structure
        notion_token = config["notion"]["api"]["token"]

        # Or use legacy compatibility methods
        legacy_config = config_manager.get_legacy_config()
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses default locations.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.env_vars_loaded = False
        self._load_environment()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path.

        Checks for src/config/notion-hugo-config.yaml first (primary), then falls back to config.yaml (unified).

        Returns:
            Path to the configuration file.
        """
        base_dir = Path(os.path.dirname(os.path.dirname(__file__)))

        # Priority order: src/config/notion-hugo-config.yaml (primary) > config.yaml (unified)
        primary_config = base_dir / "src" / "config" / "notion-hugo-config.yaml"
        unified_config = base_dir / "config.yaml"

        if primary_config.exists():
            return str(primary_config)
        elif unified_config.exists():
            return str(unified_config)
        else:
            # Default to primary config location
            return str(primary_config)

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        if not self.env_vars_loaded:
            load_dotenv()
            self.env_vars_loaded = True

    def _mask_sensitive_value(self, value: str, mask_type: str = "token") -> str:
        """Mask sensitive values for logging.

        Args:
            value: The sensitive value to mask.
            mask_type: Type of masking ('token', 'id', 'generic').

        Returns:
            Masked version of the value.
        """
        if not value:
            return "[NOT_SET]"

        if mask_type == "token":
            return f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
        elif mask_type == "id":
            return f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "****"
        else:
            return "****"

    def validate_notion_token(self, token: str) -> Tuple[bool, str]:
        """Validate Notion API token.

        Args:
            token: The Notion API token to validate.

        Returns:
            Tuple of (is_valid, message).
        """
        if not token:
            return False, "Token is not set."

        if not token.startswith("ntn_"):
            return False, "Invalid Notion token format. Must start with 'ntn_'."

        if len(token) < 50:
            return False, "Token length is too short."

        # Test API connection
        try:
            notion = Client(auth=token)
            notion.search(query="", page_size=1)
            return True, "Token is valid."
        except APIResponseError as e:
            return False, f"API call failed: {str(e)}"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    def _resolve_env_variables(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variable placeholders in configuration.

        Supports ${VAR_NAME} and ${VAR_NAME:-default_value} syntax.

        Args:
            config_data: Configuration dictionary with potential env var placeholders.

        Returns:
            Configuration dictionary with resolved environment variables.
        """

        def resolve_value(value: Any) -> Any:
            if isinstance(value, str):
                # Pattern for ${VAR_NAME} or ${VAR_NAME:-default}
                pattern = r"\$\{([^}]+)\}"
                matches = re.findall(pattern, value)

                for match in matches:
                    if ":-" in match:
                        # Handle default values
                        var_name, default_val = match.split(":-", 1)
                        env_value = os.environ.get(var_name, default_val)
                    else:
                        # No default value
                        env_value = os.environ.get(match, "")

                    value = value.replace(f"${{{match}}}", env_value)

                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value

        return resolve_value(config_data)

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides using SECTION_SUBSECTION_KEY pattern.

        Examples:
            NOTION_API_TOKEN overrides notion.api.token
            HUGO_SITE_TITLE overrides hugo.site.title
            DEPLOYMENT_GITHUB_ACTIONS_AUTO_DEPLOY overrides deployment.github_actions.auto_deploy

        Args:
            config: Configuration dictionary to apply overrides to.

        Returns:
            Configuration with environment variable overrides applied.
        """

        def set_nested_value(data: Dict[str, Any], path: List[str], value: Any) -> None:
            """Set a nested dictionary value using a path."""
            current = data
            for key in path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Try to convert the value to appropriate type
            final_key = path[-1]
            try:
                # Try boolean conversion
                if value.lower() in ("true", "false"):
                    current[final_key] = value.lower() == "true"
                # Try integer conversion
                elif value.isdigit():
                    current[final_key] = int(value)
                # Try float conversion
                elif "." in value and value.replace(".", "").isdigit():
                    current[final_key] = float(value)
                else:
                    current[final_key] = value
            except (ValueError, AttributeError):
                current[final_key] = value

        # Get all environment variables that match our patterns
        for env_key, env_value in os.environ.items():
            if not env_value:  # Skip empty values
                continue

            # Convert SECTION_SUBSECTION_KEY to section.subsection.key
            parts = env_key.lower().split("_")
            if len(parts) >= 2:
                try:
                    set_nested_value(config, parts, env_value)
                except Exception:
                    # Skip if we can't set the value (e.g., invalid path)
                    continue

        return config

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with environment variable support.

        Returns:
            Complete configuration dictionary with environment overrides applied.
        """
        self._load_environment()

        # Load base configuration from file
        config_data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load configuration file: {e}")
                config_data = {}

        # If no config file exists or it's empty, create a minimal unified structure
        if not config_data:
            config_data = self._create_default_unified_config()

        # Resolve environment variable placeholders in the config
        config_data = self._resolve_env_variables(config_data)

        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)

        return config_data

    def _create_default_unified_config(self) -> Dict[str, Any]:
        """Create a default unified configuration structure.

        Returns:
            Default unified configuration dictionary.
        """
        return {
            "notion": {
                "api": {
                    "token": "${NOTION_TOKEN:-}",
                    "timeout": 30,
                    "retry": {"max_attempts": 3, "backoff_factor": 2},
                },
                "mount": {
                    "auto_discovery": {"enabled": False, "parent_page_url": ""},
                    "databases": [],
                    "pages": [],
                },
                "sync": {
                    "mode": "smart",
                    "batch_size": 10,
                    "include_drafts": False,
                    "filters": {
                        "status_filter": ["Published", "Live"],
                        "date_range": {
                            "enabled": False,
                            "from": "2020-01-01",
                            "to": None,
                        },
                    },
                },
            },
            "hugo": {
                "site": {
                    "base_url": "https://example.com",
                    "title": "My Blog",
                    "description": "A blog powered by Notion and Hugo",
                    "language": "en",
                    "author": "Author Name",
                },
                "theme": {
                    "name": "PaperMod",
                    "params": {
                        "env": "production",
                        "default_theme": "auto",
                        "show_reading_time": True,
                        "show_share_buttons": True,
                        "show_post_nav_links": True,
                        "show_breadcrumbs": True,
                        "show_code_copy_buttons": True,
                        "show_word_count": True,
                        "show_toc": False,
                        "disable_theme_toggle": False,
                    },
                },
                "content": {
                    "markdown": {
                        "renderer": "goldmark",
                        "goldmark": {
                            "extensions": {
                                "definition_list": True,
                                "footnote": True,
                                "linkify": True,
                                "strikethrough": True,
                                "table": True,
                                "task_list": True,
                                "typographer": True,
                            },
                            "parser": {
                                "auto_heading_id": True,
                                "auto_heading_id_type": "github",
                            },
                            "renderer": {"unsafe": True},
                        },
                    },
                    "highlight": {
                        "style": "monokai",
                        "line_numbers": True,
                        "code_fences": True,
                        "guess_syntax": True,
                    },
                    "math": {
                        "enabled": True,
                        "block_delimiters": ["\\[", "\\]"],
                        "inline_delimiters": ["\\(", "\\)"],
                        "copy_tex": True,
                        "mhchem": True,
                    },
                },
                "menu": {
                    "main": [
                        {"name": "posts", "url": "/posts/", "weight": 5},
                        {"name": "tags", "url": "/tags/", "weight": 20},
                    ]
                },
                "seo": {
                    "google_analytics": {"site_verification_tag": ""},
                    "sitemap": {"change_frequency": "weekly", "priority": 0.5},
                },
                "urls": {
                    "permalinks": {"posts": ":sections/:slug", "pages": ":slug"},
                    "filename": {
                        "format": "date-title",
                        "date_format": "%Y-%m-%d",
                        "korean_title_mode": "slug",
                    },
                },
            },
            "content": {
                "images": {
                    "optimization": True,
                    "formats": ["jpg", "jpeg", "png", "webp"],
                    "max_width": 1200,
                    "quality": 85,
                },
                "files": {
                    "allowed_extensions": [
                        ".md",
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".svg",
                        ".pdf",
                    ],
                    "max_file_size": 10,
                },
                "validation": {
                    "required_fields": ["title", "date"],
                    "validate_markdown": True,
                },
            },
            "deployment": {
                "strategy": "github_actions",
                "github_actions": {
                    "auto_deploy": True,
                    "trigger": "push",
                    "branch": "main",
                    "hugo_version": "0.140.0",
                    "hugo_extended": True,
                },
                "schedule": {"enabled": True, "cron": "0 */2 * * *", "timezone": "UTC"},
                "build": {
                    "environment": "production",
                    "enable_git_info": True,
                    "build_drafts": False,
                    "build_future": False,
                },
            },
            "development": {
                "server": {"port": 1313, "host": "localhost", "watch": True},
                "debug": {"verbose": False, "log_level": "info", "profiling": False},
                "docker": {
                    "image": "notion-hugo:latest",
                    "ports": ["1313:1313"],
                    "volumes": [
                        "./:/app",
                        "./src/config/.notion-hugo-state.json:/app/src/config/.notion-hugo-state.json",
                    ],
                },
            },
            "security": {
                "environment_variables": {
                    "use_env_vars": True,
                    "validate_env_vars": True,
                },
                "logging": {
                    "mask_sensitive_data": True,
                    "mask_patterns": [
                        "ntn_[a-zA-Z0-9]+",
                        "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
                    ],
                },
                "data": {
                    "backup_config": True,
                    "encryption": {"enabled": False, "algorithm": "AES-256-GCM"},
                },
            },
            "features": {
                "experimental": {
                    "graphql_api": False,
                    "advanced_caching": False,
                    "plugin_system": False,
                },
                "legacy": {"old_config_support": True, "legacy_api": False},
            },
            "metadata": {
                "config_version": "2.0.0",
                "generated_at": "${CONFIG_GENERATED_AT:-}",
                "generated_by": "notion-hugo-cli",
                "last_updated": "${CONFIG_LAST_UPDATED:-}",
                "compatibility": {
                    "min_notion_hugo_version": "1.0.0",
                    "hugo_version_range": ">=0.120.0",
                    "python_version_range": ">=3.8",
                },
            },
        }

    def get_legacy_config(self) -> LegacyConfig:
        """Get configuration in legacy format for backward compatibility.

        Returns:
            Configuration in legacy format.
        """
        unified_config = self.load_config()

        # Convert unified config to legacy format
        legacy_config: LegacyConfig = {
            "mount": {"databases": [], "pages": []},
            "filename": {
                "format": "date-title",
                "date_format": "%Y-%m-%d",
                "korean_title": "slug",
            },
            "deployment": {
                "auto_deploy": True,
                "trigger": "push",
                "schedule": None,
                "environment": "production",
            },
            "security": {
                "use_environment_variables": True,
                "mask_sensitive_logs": True,
                "token_validation": True,
            },
        }

        # Map from unified structure to legacy structure
        try:
            # Map databases
            if "notion" in unified_config and "mount" in unified_config["notion"]:
                databases = unified_config["notion"]["mount"].get("databases", [])
                for db in databases:
                    if "database_id" in db and "target_folder" in db:
                        legacy_config["mount"]["databases"].append(
                            {
                                "database_id": db["database_id"],
                                "target_folder": db["target_folder"],
                            }
                        )

                # Map pages
                pages = unified_config["notion"]["mount"].get("pages", [])
                for page in pages:
                    if "page_id" in page and "target_file" in page:
                        legacy_config["mount"]["pages"].append(
                            {
                                "page_id": page["page_id"],
                                "target_folder": page.get("target_file", "."),
                            }
                        )

            # Map filename config from Hugo URLs section
            if "hugo" in unified_config and "urls" in unified_config["hugo"]:
                filename_config = unified_config["hugo"]["urls"].get("filename", {})
                if filename_config:
                    legacy_config["filename"].update(
                        {
                            "format": filename_config.get("format", "date-title"),
                            "date_format": filename_config.get(
                                "date_format", "%Y-%m-%d"
                            ),
                            "korean_title": filename_config.get(
                                "korean_title_mode", "slug"
                            ),
                        }
                    )

            # Map deployment config
            if "deployment" in unified_config:
                deploy_config = unified_config["deployment"]
                github_actions = deploy_config.get("github_actions", {})
                schedule = deploy_config.get("schedule", {})
                build = deploy_config.get("build", {})

                legacy_config["deployment"].update(
                    {
                        "auto_deploy": github_actions.get("auto_deploy", True),
                        "trigger": github_actions.get("trigger", "push"),
                        "schedule": (
                            schedule.get("cron") if schedule.get("enabled") else None
                        ),
                        "environment": build.get("environment", "production"),
                    }
                )

            # Map security config
            if "security" in unified_config:
                security_config = unified_config["security"]
                env_vars = security_config.get("environment_variables", {})
                logging = security_config.get("logging", {})

                legacy_config["security"].update(
                    {
                        "use_environment_variables": env_vars.get("use_env_vars", True),
                        "mask_sensitive_logs": logging.get("mask_sensitive_data", True),
                        "token_validation": env_vars.get("validate_env_vars", True),
                    }
                )

        except Exception as e:
            print(f"Warning: Error mapping unified config to legacy format: {e}")

        return legacy_config

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment readiness status.

        Returns:
            Dictionary containing deployment status information.
        """
        status = {
            "environment_ready": False,
            "notion_token_valid": False,
            "databases_configured": False,
            "ready_to_deploy": False,
            "missing_items": [],
        }

        # Check environment variables
        notion_token = os.environ.get("NOTION_TOKEN")
        if notion_token:
            is_valid, message = self.validate_notion_token(notion_token)
            status["notion_token_valid"] = is_valid
            if not is_valid:
                status["missing_items"].append(f"Notion token issue: {message}")
        else:
            status["missing_items"].append("NOTION_TOKEN environment variable required")

        # Check database configuration
        config = self.load_config()
        if "notion" in config and "mount" in config["notion"]:
            databases = config["notion"]["mount"].get("databases", [])
            if databases:
                status["databases_configured"] = True
            else:
                status["missing_items"].append("Database configuration required")
        else:
            status["missing_items"].append("Database configuration required")

        # Overall status
        status["environment_ready"] = (
            status["notion_token_valid"] and status["databases_configured"]
        )
        status["ready_to_deploy"] = (
            status["environment_ready"] and len(status["missing_items"]) == 0
        )

        return status

    def create_env_template(self) -> None:
        """Create environment variable template file."""
        template_content = """# Notion-Hugo Environment Variables Configuration
# Copy this file to .env and fill in your actual values

# 🔴 Required: Notion API Token
NOTION_TOKEN=your_notion_token_here

# 🟡 Auto-generated: Database IDs (automatically set after setup.py)
NOTION_DATABASE_ID_POSTS=auto_generated_database_id

# 🟢 Optional: Hugo Configuration
HUGO_VERSION=0.140.0
HUGO_ENV=production
HUGO_EXTENDED=true

# 🟢 Optional: Deployment Configuration  
DEPLOY_ENVIRONMENT=production

# 🟢 Optional: Site Configuration
HUGO_SITE_BASE_URL=https://yourdomain.com
HUGO_SITE_TITLE=Your Blog Title
HUGO_SITE_DESCRIPTION=Your blog description
HUGO_SITE_AUTHOR=Your Name

# 🟢 Optional: Security Settings
SECURITY_LOGGING_MASK_SENSITIVE_DATA=true
SECURITY_ENVIRONMENT_VARIABLES_VALIDATE_ENV_VARS=true
"""

        with open(".env.template", "w", encoding="utf-8") as f:
            f.write(template_content)

        print("✅ Environment variable template created: .env.template")

    def create_default_config_if_missing(self) -> None:
        """Create default configuration file if it doesn't exist."""
        if not os.path.exists(self.config_path):
            default_config = self._create_default_unified_config()

            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            print(f"✅ Default unified configuration created: {self.config_path}")

    def get_hugo_directories(self) -> Dict[str, str]:
        """Get Hugo directory paths from configuration.

        Returns:
            Dictionary containing Hugo directory paths with fallback defaults.
        """
        config = self.load_config()

        # Default directory structure
        defaults = {
            "root": "blog",
            "content": "content",
            "public": "public",
            "static": "static",
            "themes": "themes",
        }

        # Get Hugo directories from config with fallbacks
        hugo_config = config.get("hugo", {})
        directories = hugo_config.get("directories", {})

        # Merge with defaults
        result = defaults.copy()
        result.update(directories)

        return result

    def get_hugo_root_path(self) -> str:
        """Get the Hugo project root directory path.

        Returns:
            Path to Hugo root directory (e.g., "blog").
        """
        return self.get_hugo_directories()["root"]

    def get_hugo_content_path(self) -> str:
        """Get the full path to Hugo content directory.

        Returns:
            Full path to content directory (e.g., "blog/content").
        """
        dirs = self.get_hugo_directories()
        return os.path.join(dirs["root"], dirs["content"])

    def get_hugo_public_path(self) -> str:
        """Get the full path to Hugo public directory.

        Returns:
            Full path to public directory (e.g., "blog/public").
        """
        dirs = self.get_hugo_directories()
        return os.path.join(dirs["root"], dirs["public"])

    def get_hugo_static_path(self) -> str:
        """Get the full path to Hugo static directory.

        Returns:
            Full path to static directory (e.g., "blog/static").
        """
        dirs = self.get_hugo_directories()
        return os.path.join(dirs["root"], dirs["static"])

    def create_gitmodules_file(self) -> None:
        """Create .gitmodules file with dynamic Hugo root path."""
        hugo_root = self.get_hugo_root_path()
        theme_name = "PaperMod"
        theme_url = "https://github.com/adityatelange/hugo-PaperMod.git"

        gitmodules_content = f"""[submodule "{hugo_root}/themes/{theme_name}"]
	path = {hugo_root}/themes/{theme_name}
	url = {theme_url}
"""

        with open(".gitmodules", "w", encoding="utf-8") as f:
            f.write(gitmodules_content)

        print(f"✅ Created .gitmodules with Hugo root: {hugo_root}")

    def get_theme_path(self) -> str:
        """Get the full path to the theme directory.

        Returns:
            Full path to theme directory (e.g., "blog/themes/PaperMod").
        """
        dirs = self.get_hugo_directories()
        config = self.load_config()
        theme_name = config.get("hugo", {}).get("theme", {}).get("name", "PaperMod")
        return os.path.join(dirs["root"], dirs["themes"], theme_name)


# Convenience functions for backward compatibility
def load_config() -> LegacyConfig:
    """Load configuration in legacy format for backward compatibility.

    Returns:
        Configuration in legacy format.
    """
    manager = ConfigManager()
    return manager.get_legacy_config()


def create_config_file(config: Dict[str, Any]) -> None:
    """Create configuration file for backward compatibility.

    Args:
        config: Configuration dictionary to save.
    """
    manager = ConfigManager()

    with open(manager.config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


# Diagnostic and utility functions
def diagnose_configuration() -> Dict[str, Any]:
    """Run configuration diagnostics.

    Returns:
        Dictionary containing diagnostic results.
    """
    print("🔍 Notion-Hugo Configuration Diagnostics\n")

    manager = ConfigManager()

    # 1. Environment variables check
    print("1. Environment Variables:")
    notion_token = os.environ.get("NOTION_TOKEN")
    if notion_token:
        print(f"   ✅ NOTION_TOKEN: {manager._mask_sensitive_value(notion_token)}")

        is_valid, message = manager.validate_notion_token(notion_token)
        if is_valid:
            print(f"   ✅ Token validation: {message}")
        else:
            print(f"   ❌ Token validation: {message}")
    else:
        print("   ❌ NOTION_TOKEN: Not set")

    # 2. Configuration file check
    print("\n2. Configuration File:")
    if os.path.exists(manager.config_path):
        print(f"   ✅ Config file: {manager.config_path}")
        try:
            config = manager.load_config()
            print("   ✅ Config loading: Success")

            # Check if it's unified or legacy
            if "notion" in config and "hugo" in config:
                print("   📊 Config type: Unified (config.yaml)")
                databases = (
                    config.get("notion", {}).get("mount", {}).get("databases", [])
                )
                print(f"   📊 Databases: {len(databases)} configured")
            else:
                print("   📊 Config type: Unified (src/config/notion-hugo-config.yaml)")
                databases = (
                    config.get("notion", {}).get("mount", {}).get("databases", [])
                )
                print(f"   📊 Databases: {len(databases)} configured")

        except Exception as e:
            print(f"   ❌ Config loading: Failed - {e}")
    else:
        print(f"   ⚠️ Config file: Missing - Will use defaults")

    # 3. Deployment status check
    print("\n3. Deployment Readiness:")
    status = manager.get_deployment_status()

    if status["ready_to_deploy"]:
        print("   ✅ Ready for deployment!")
    else:
        print("   ❌ Not ready for deployment:")
        for item in status["missing_items"]:
            print(f"      - {item}")

    print("\n" + "=" * 50)

    return status


if __name__ == "__main__":
    # Run diagnostics
    diagnose_configuration()
