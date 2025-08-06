"""
Notion-Hugo Flow Package

A modern CLI application for bidirectional sync between Notion and Hugo static sites.
Supports local-first workflows optimized for LLM-assisted content creation.
"""

__version__ = "1.0.0"
__author__ = "Gunn Kim"
__description__ = "Modern blog publishing with bidirectional sync between Notion, local markdown, and Hugo"

from .app import cli

__all__ = ["cli"]