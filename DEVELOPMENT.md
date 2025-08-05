# Local Development Setup Guide for Notion-Hugo Blog

## 1. Prerequisites

### System Requirements
- Python 3.8+ (3.11+ recommended)
- Hugo extended version
- Git
- Notion account with API access

### Install Dependencies

#### Python Environment
```bash
# Recommended: Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install project dependencies
pip install -e .  # Editable install
# Or with uv (recommended for faster dependency resolution)
uv add -e .
```

#### Hugo Installation
```bash
# macOS (Homebrew)
brew install hugo

# Linux
sudo apt-get install hugo

# Windows
choco install hugo-extended
```

## 2. Environment Configuration

### 2.1 Notion API Setup
1. Create a Notion integration:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Click "Create new integration"
   - Name your integration
   - Copy the **Internal Integration Token**

2. Create a `.env` file in the project root:
```bash
# .env
NOTION_TOKEN=your_internal_integration_token
NOTION_DATABASE_ID_POSTS=your_notion_database_id
```

### 2.2 Notion Database Preparation
- Create a database in Notion
- Share the database with your Notion integration
- Copy the database ID from the URL

## 3. Local Development Workflow

### Notion Sync
```bash
# Sync Notion content to markdown
python notion_hugo_app.py --notion-only

# Full sync (force processing all pages)
python notion_hugo_app.py --full-sync

# Incremental sync (default behavior)
python notion_hugo_app.py
```

### Hugo Local Development
```bash
# Start Hugo development server
python notion_hugo_app.py --hugo-args="server --minify"

# Alternative: Direct Hugo command
hugo server --minify
```

## 4. Testing Checklist

### Content Validation
- [ ] All Notion pages sync correctly
- [ ] Markdown files generated in `content/posts/`
- [ ] Front matter is correctly populated
- [ ] Images and assets transferred

### Hugo Build Verification
```bash
# Build site for production
python notion_hugo_app.py --hugo-only

# Or directly
hugo --minify
```

## 5. Troubleshooting

### Common Issues

#### Notion API Errors
- **Invalid Token**: Double-check your Notion integration token
- **Database Access**: Ensure the integration has access to the database
- **Rate Limits**: Respect Notion's API rate limits

#### Build Failures
- Check Hugo version (extended version required)
- Verify markdown front matter syntax
- Inspect error messages in console

### Debugging Options
```bash
# Verbose output for diagnosis
python notion_hugo_app.py --verbose

# Dry run to check changes without processing
python notion_hugo_app.py --dry-run
```

## 6. Development Best Practices
- Always work in a feature branch
- Run linters: `ruff check .`
- Format code: `ruff format .`
- Type check: `mypy .`
- Run tests: `pytest tests/`

## 7. Deployment Readiness
- Commit all changes to Git
- Push to GitHub
- GitHub Actions will handle deployment

---

**Pro Tip**: Use `--interactive` flag for guided setup:
```bash
python notion_hugo_app.py --interactive
```