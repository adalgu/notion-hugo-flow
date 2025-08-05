#!/usr/bin/env python3
"""
Notion-Hugo Integration Pipeline

This application converts content from Notion to Hugo-compatible markdown and builds
a Hugo site. It serves as the main entry point for the Notion-Hugo pipeline.

Usage:
    python notion_hugo_app.py [options]

Options:
    --notion-only        Only run Notion to Markdown conversion
    --hugo-only          Only run Hugo preprocessing and build
    --no-build           Skip Hugo build stage
    --hugo-args="..."    Arguments to pass to Hugo (e.g. --hugo-args="server --minify")
    --incremental        Only process changed pages (default)
    --full-sync          Force processing all pages
    --state-file=FILE    Metadata file path (default: .notion-hugo-state.json)
    --dry-run            Check for changes without actually processing
    --setup-db           Create and set up a new Notion database
    --migrate-db         Migrate from an existing Notion database
    --interactive, -i    Run in interactive setup mode
    --verbose            Enable verbose output
    --quiet              Minimal output (errors only)
"""

from src.notion_hugo import main

if __name__ == "__main__":
    main()
