# Project Brief

## Project Name
Notion-Hugo Integration Pipeline

## Core Goals
- Convert Notion databases/pages to Markdown.
- Handle error files before Hugo build.
- Provide a complete build pipeline using Python.

## Key Features
- Incremental rendering based on `last_edited_time` and content hash.
- Clean repository structure with only final Hugo build results deployed to GitHub Pages.
- Automated deployment using GitHub Actions.
