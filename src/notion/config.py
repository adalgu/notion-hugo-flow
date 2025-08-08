"""
Notion Pipeline Configuration

Handles configuration for the Notion pipeline including API settings,
sync options, and content filters.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class NotionConfig:
    """Configuration for Notion pipeline operations."""

    # API Configuration
    token: str
    timeout: int = 30
    retry_attempts: int = 3
    retry_backoff: float = 2.0

    # Sync Configuration
    database_id: Optional[str] = None
    sync_mode: str = "incremental"  # incremental | full
    batch_size: int = 50
    include_drafts: bool = False

    # Content Filters
    status_filter: List[str] = field(default_factory=lambda: ["Published", "Live"])
    date_range: Optional[Dict[str, str]] = None

    # Output Configuration
    output_dir: str = "blog/content/posts"
    markdown_format: str = "hugo"  # hugo | standard

    # State Management
    state_file: str = ".notion-sync-state.json"

    @classmethod
    def from_file(cls, config_path: str) -> "NotionConfig":
        """Load configuration from YAML file."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data.get("notion", {}))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotionConfig":
        """Create configuration from dictionary."""
        return cls(
            token=data.get("token", ""),
            timeout=data.get("timeout", 30),
            retry_attempts=data.get("retry", {}).get("max_attempts", 3),
            retry_backoff=data.get("retry", {}).get("backoff_factor", 2.0),
            database_id=data.get("database_id"),
            sync_mode=data.get("sync", {}).get("mode", "incremental"),
            batch_size=data.get("sync", {}).get("batch_size", 50),
            include_drafts=data.get("sync", {}).get("include_drafts", False),
            status_filter=data.get("sync", {})
            .get("filters", {})
            .get("status_filter", ["Published", "Live"]),
            date_range=data.get("sync", {}).get("filters", {}).get("date_range"),
            output_dir=data.get("output_dir", "blog/content/posts"),
            markdown_format=data.get("markdown_format", "hugo"),
            state_file=data.get("state_file", ".notion-sync-state.json"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "token": self.token,
            "timeout": self.timeout,
            "retry": {
                "max_attempts": self.retry_attempts,
                "backoff_factor": self.retry_backoff,
            },
            "database_id": self.database_id,
            "sync": {
                "mode": self.sync_mode,
                "batch_size": self.batch_size,
                "include_drafts": self.include_drafts,
                "filters": {
                    "status_filter": self.status_filter,
                    "date_range": self.date_range,
                },
            },
            "output_dir": self.output_dir,
            "markdown_format": self.markdown_format,
            "state_file": self.state_file,
        }

    def save(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"notion": self.to_dict()}

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.token:
            errors.append("Notion API token is required")
        elif not self.token.startswith("ntn_"):
            errors.append("Invalid Notion API token format (should start with 'ntn_')")

        if self.database_id and len(self.database_id) != 32:
            errors.append("Invalid database ID format")

        if self.sync_mode not in ["incremental", "full"]:
            errors.append("Sync mode must be 'incremental' or 'full'")

        if self.batch_size <= 0 or self.batch_size > 100:
            errors.append("Batch size must be between 1 and 100")

        if self.timeout <= 0:
            errors.append("Timeout must be positive")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


def load_notion_config(config_path: Optional[str] = None) -> NotionConfig:
    """Load Notion configuration from file or environment."""

    # Try to load from specified path
    if config_path:
        return NotionConfig.from_file(config_path)

    # Try default config locations
    default_paths = ["src/config/notion.yaml", "config/notion.yaml", "notion.yaml"]

    for path in default_paths:
        if Path(path).exists():
            return NotionConfig.from_file(path)

    # Try to create from environment variables
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("Notion API token not found in configuration or environment")

    return NotionConfig(
        token=token,
        database_id=os.getenv("NOTION_DATABASE_ID"),
        output_dir=os.getenv("NOTION_OUTPUT_DIR", "blog/content/posts"),
    )
