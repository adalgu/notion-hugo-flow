"""
Hugo Pipeline Module

This module handles the building of Hugo static sites from markdown content.
It provides a clean interface for Hugo build operations and development server management.

Core Components:
- pipeline.py: Main pipeline orchestration  
- builder.py: Hugo build logic
- server.py: Development server management
- config.py: Hugo-specific configuration management
"""

from .pipeline import HugoPipeline
from .config import HugoConfig

__version__ = "1.0.0"
__all__ = ["HugoPipeline", "HugoConfig"]