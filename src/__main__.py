#!/usr/bin/env python3
"""
Entry point for the Notion-Hugo CLI application.

This allows the application to be run as a module:
    python -m src
"""

from .app import cli

if __name__ == "__main__":
    cli()