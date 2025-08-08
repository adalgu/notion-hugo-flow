"""
Notion Pipeline Configuration

Manages configuration for Notion API integration and content sync.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NotionConfig:
    """Configuration for Notion pipeline"""
    
    # Required fields
    token: Optional[str] = None
    database_id: Optional[str] = None
    
    # Sync configuration
    sync_mode: str = "incremental"  # "incremental" or "full"
    batch_size: int = 50
    include_drafts: bool = False
    
    # Output configuration
    output_dir: str = "blog/content/posts"
    markdown_format: str = "hugo"  # "hugo" or "standard"
    
    # Filter configuration
    status_filters: List[str] = field(default_factory=lambda: ["Published", "Live"])
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    
    # Advanced options
    rate_limit_delay: float = 0.1  # seconds between API calls
    max_retries: int = 3
    timeout: int = 30
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        if config_dict:
            # Map config dictionary to attributes
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Ensure output directory is a Path object
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(self.token and self.database_id)
    
    @property
    def filters(self) -> Dict[str, Any]:
        """Get API filters based on configuration"""
        filters = {}
        
        if self.status_filters:
            filters["status"] = self.status_filters
        
        if self.date_from or self.date_to:
            filters["date_range"] = {
                "from": self.date_from,
                "to": self.date_to
            }
        
        return filters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "token": self.token,
            "database_id": self.database_id,
            "sync_mode": self.sync_mode,
            "batch_size": self.batch_size,
            "include_drafts": self.include_drafts,
            "output_dir": str(self.output_dir),
            "markdown_format": self.markdown_format,
            "status_filters": self.status_filters,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.token:
            errors.append("Notion API token is required")
        
        if not self.database_id:
            errors.append("Notion database ID is required")
        
        if self.sync_mode not in ["incremental", "full"]:
            errors.append("sync_mode must be 'incremental' or 'full'")
        
        if self.batch_size < 1 or self.batch_size > 100:
            errors.append("batch_size must be between 1 and 100")
        
        if self.markdown_format not in ["hugo", "standard"]:
            errors.append("markdown_format must be 'hugo' or 'standard'")
        
        return errors