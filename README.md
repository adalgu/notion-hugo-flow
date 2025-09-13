# Notion-Hugo Flow

> Transform your Notion workspace into a blazing-fast Hugo blog with smart automation and bidirectional sync.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Hugo](https://img.shields.io/badge/Hugo-Extended-FF4088?logo=hugo&logoColor=white)](https://gohugo.io)
[![Notion API](https://img.shields.io/badge/Notion-API%20v2-000000?logo=notion&logoColor=white)](https://developers.notion.com)

## Features

- 🚀 **5-Stage Pipeline** - Clean separation: Notion → Markdown → Hugo → Build → Deploy
- 🔄 **Incremental Sync** - Only processes changed content for efficiency
- 🎯 **Zero Config** - Auto-detects environment and applies optimal settings
- 📦 **Multi-Platform** - Deploy to GitHub Pages, Vercel, Netlify, or custom hosting
- 🎨 **Theme Ready** - Works with any Hugo theme, PaperMod included
- 🔍 **SEO Optimized** - Structured data, meta tags, and sitemaps
- 🤖 **LLM Ready** - Optimized for AI-assisted content creation

## Quick Start

### Installation

```bash
pip install notion-hugo-flow
```

### Setup

1. **Get Notion API Token**: [Create integration](https://www.notion.so/my-integrations)
2. **Create Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your Notion token and database ID
   ```

3. **Run Pipeline**:
   ```bash
   # Complete pipeline
   notion-hugo run --full

   # Or step by step
   notion-hugo notion     # Sync from Notion
   notion-hugo process    # Process for Hugo
   notion-hugo integrate  # Integrate content
   notion-hugo build      # Build Hugo site
   notion-hugo deploy     # Deploy site
   ```

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.
