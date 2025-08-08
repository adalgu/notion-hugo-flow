"""
Notion Pipeline Module

This module handles the conversion of Notion database content to Hugo-compatible markdown files.
It provides a clean interface for syncing data from Notion API to local markdown files.

Core Components:
- pipeline.py: Main pipeline orchestration
- sync.py: Notion API synchronization logic
- converter.py: Notion to Markdown conversion
- config.py: Notion-specific configuration management
"""

from .pipeline import NotionPipeline
from .config import NotionConfig

__version__ = "1.0.0"
__all__ = ["NotionPipeline", "NotionConfig"]