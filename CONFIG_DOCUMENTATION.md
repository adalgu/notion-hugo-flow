# Unified Configuration Documentation

This document provides comprehensive documentation for the unified `config.yaml` structure that consolidates all Notion-Hugo configuration settings.

## Overview

The unified configuration system provides:
- **Single source of truth** for all settings
- **Environment variable support** with automatic override capability
- **Smart defaults** for 5-minute setup flow
- **Logical grouping** of related settings
- **Backward compatibility** with existing configurations

## Environment Variable Override Pattern

Any configuration value can be overridden using environment variables following the pattern:
```
SECTION_SUBSECTION_KEY=value
```

### Examples:
- `NOTION_API_TOKEN` overrides `notion.api.token`
- `HUGO_SITE_BASE_URL` overrides `hugo.site.base_url`
- `DEPLOYMENT_GITHUB_ACTIONS_AUTO_DEPLOY` overrides `deployment.github_actions.auto_deploy`

## Configuration Sections

### 1. Notion Integration Settings (`notion`)

Controls how the system interacts with Notion API and processes content from Notion databases.

#### Key Settings:
- **`notion.api.token`**: Your Notion integration token (use `NOTION_TOKEN` env var)
- **`notion.mount.databases`**: List of Notion databases to sync
- **`notion.sync.mode`**: Choose between "smart" (incremental) or "full" sync

#### Example:
```yaml
notion:
  api:
    token: "${NOTION_TOKEN}"
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS}"
        target_folder: "posts"
  sync:
    mode: "smart"
    batch_size: 10
```

### 2. Hugo Site Configuration (`hugo`)

All Hugo-related settings including theme, content processing, and site metadata.

#### Key Settings:
- **`hugo.site.base_url`**: Your website's base URL
- **`hugo.theme.name`**: Hugo theme to use (default: "PaperMod")
- **`hugo.content.markdown`**: Markdown processing settings
- **`hugo.seo`**: SEO and analytics configuration

#### Example:
```yaml
hugo:
  site:
    base_url: "https://yourdomain.com"
    title: "Your Blog Title"
  theme:
    name: "PaperMod"
    params:
      show_reading_time: true
      show_toc: true
```

### 3. Content Processing Settings (`content`)

Controls how content is processed, validated, and optimized.

#### Key Settings:
- **`content.images.optimization`**: Enable automatic image optimization
- **`content.files.allowed_extensions`**: File types allowed for sync
- **`content.validation.required_fields`**: Required frontmatter fields

#### Example:
```yaml
content:
  images:
    optimization: true
    max_width: 1200
    quality: 85
  validation:
    required_fields: ["title", "date"]
```

### 4. Deployment Configuration (`deployment`)

Settings for how and when your blog is deployed.

#### Key Settings:
- **`deployment.strategy`**: Deployment method ("github_actions" recommended)
- **`deployment.schedule.enabled`**: Enable automatic scheduled sync
- **`deployment.build.environment`**: Build environment ("production" or "development")

#### Example:
```yaml
deployment:
  strategy: "github_actions"
  github_actions:
    auto_deploy: true
    hugo_version: "0.140.0"
  schedule:
    enabled: true
    cron: "0 */2 * * *"  # Every 2 hours
```

### 5. Development Settings (`development`)

Local development and debugging configuration.

#### Key Settings:
- **`development.server.port`**: Local development server port
- **`development.debug.log_level`**: Logging verbosity
- **`development.docker`**: Docker container settings

#### Example:
```yaml
development:
  server:
    port: 1313
    watch: true
  debug:
    log_level: "info"
    verbose: false
```

### 6. Security and Privacy Settings (`security`)

Security-related configuration including data masking and environment variable handling.

#### Key Settings:
- **`security.logging.mask_sensitive_data`**: Hide sensitive data in logs
- **`security.environment_variables.use_env_vars`**: Prefer environment variables
- **`security.data.backup_config`**: Backup configuration changes

#### Example:
```yaml
security:
  logging:
    mask_sensitive_data: true
  environment_variables:
    use_env_vars: true
    validate_env_vars: true
```

## Quick Setup Examples

### Minimal Configuration (5-minute setup)
```yaml
notion:
  api:
    token: "${NOTION_TOKEN}"
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS}"
        target_folder: "posts"

hugo:
  site:
    base_url: "https://yourdomain.com"
    title: "My Blog"
```

### Production Configuration
```yaml
notion:
  api:
    token: "${NOTION_TOKEN}"
    timeout: 30
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS}"
        target_folder: "posts"
        property_mapping:
          title: "Name"
          status: "Status"
          tags: "Tags"
  sync:
    mode: "smart"
    include_drafts: false
    filters:
      status_filter: ["Published"]

hugo:
  site:
    base_url: "https://yourdomain.com"
    title: "Professional Blog"
    description: "Insights and updates"
  theme:
    name: "PaperMod"
    params:
      env: "production"
      show_reading_time: true
      show_share_buttons: true
  seo:
    google_analytics:
      site_verification_tag: "G-XXXXXXXXXX"

deployment:
  strategy: "github_actions"
  github_actions:
    auto_deploy: true
    hugo_version: "0.140.0"
  schedule:
    enabled: true
    cron: "0 */2 * * *"

security:
  logging:
    mask_sensitive_data: true
  environment_variables:
    use_env_vars: true
```

## Migration from Existing Configurations

### From `notion-hugo.config.yaml`
The old configuration structure maps to the new structure as follows:

| Old Path | New Path |
|----------|----------|
| `mount.databases` | `notion.mount.databases` |
| `filename.format` | `hugo.urls.filename.format` |
| `sync.mode` | `notion.sync.mode` |
| `deployment.auto_deploy` | `deployment.github_actions.auto_deploy` |

### From Hugo config files
Hugo configuration files in `blog/config/_default/` are consolidated:

| Old File | New Section |
|----------|-------------|
| `config.yml` | `hugo.site`, `hugo.theme`, `hugo.menu` |
| `params.toml` | `hugo.content.math` |
| `markup.toml` | `hugo.content.markdown`, `hugo.content.highlight` |
| `permalinks.toml` | `hugo.urls.permalinks` |

## Environment Variable Template

Create a `.env` file with the following template:

```bash
# Required: Notion API Token
NOTION_TOKEN=your_notion_token_here

# Required: Database IDs (generated during setup)
NOTION_DATABASE_ID_POSTS=your_database_id_here

# Optional: Site Configuration
HUGO_SITE_BASE_URL=https://yourdomain.com
HUGO_SITE_TITLE="Your Blog Title"

# Optional: Deployment Settings
DEPLOYMENT_GITHUB_ACTIONS_AUTO_DEPLOY=true
DEPLOYMENT_SCHEDULE_ENABLED=true

# Optional: Development Settings
DEVELOPMENT_DEBUG_LOG_LEVEL=info
DEVELOPMENT_SERVER_PORT=1313
```

## Validation and Defaults

The configuration system provides:

1. **Smart Defaults**: All optional settings have sensible defaults
2. **Environment Variable Validation**: Required environment variables are checked
3. **Schema Validation**: Configuration structure is validated on load
4. **Backward Compatibility**: Legacy configuration formats are supported

## Advanced Features

### Custom Property Mapping
Map Notion database properties to content fields:

```yaml
notion:
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS}"
        property_mapping:
          title: "Post Title"      # Notion property name
          status: "Publication Status"
          author: "Author"
          tags: "Topic Tags"
```

### Content Filtering
Filter content based on various criteria:

```yaml
notion:
  sync:
    filters:
      status_filter: ["Published", "Ready"]
      date_range:
        enabled: true
        from: "2023-01-01"
        to: null  # No end date
```

### Feature Flags
Enable experimental features:

```yaml
features:
  experimental:
    graphql_api: true
    advanced_caching: true
    plugin_system: false
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   - Ensure `.env` file is in the project root
   - Check that variable names match the pattern `SECTION_SUBSECTION_KEY`

2. **Configuration Not Found**
   - Verify `config.yaml` is in the project root
   - Check file permissions and encoding (UTF-8)

3. **Invalid Configuration Values**
   - Use the validation command: `python app.py validate`
   - Check log output for specific error messages

### Debug Commands

```bash
# Validate configuration
python app.py validate

# Show current configuration
python app.py config show

# Test Notion connection
python app.py notion test-connection

# Diagnose setup issues
python app.py diagnose
```

## Configuration Precedence

Settings are applied in this order (highest to lowest priority):

1. **Environment Variables** (`NOTION_TOKEN=...`)
2. **Command Line Arguments** (`--token=...`)
3. **Configuration File** (`config.yaml`)
4. **Default Values** (built-in defaults)

This allows for flexible deployment scenarios where sensitive values come from environment variables while structure comes from the configuration file.