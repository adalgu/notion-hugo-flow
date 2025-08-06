"""
Notion-Hugo Integration Package

A modern CLI application for converting Notion pages to Hugo static sites.
"""

__version__ = "1.0.0"
__author__ = "Gunn Kim"
__description__ = "Modern blog publishing with Notion as CMS and Hugo as static site generator"

from .app import cli

__all__ = ["cli"]