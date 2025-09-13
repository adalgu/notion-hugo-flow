#!/usr/bin/env python3
"""
Modern Configuration Schema and Validation System for Notion-Hugo Phase 2

This module provides TypeScript-style configuration interfaces and Pydantic validation
for the 5-stage pipeline architecture. It supports multi-environment configuration,
legacy migration, and comprehensive validation.

Architecture:
- Unified configuration schema with stage-specific sections
- Environment variable mapping with SECTION_SUBSECTION_KEY pattern
- Type-safe validation with Pydantic models
- Legacy configuration compatibility layer
- Runtime health checks and dependency detection

Usage:
    from src.config.schema import ConfigurationManager, PipelineConfig
    
    config_manager = ConfigurationManager()
    config = config_manager.load_validated_config()
    
    # Access typed configuration
    notion_config = config.pipelines.notion
    hugo_config = config.pipelines.hugo
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Union, Literal, TypedDict
from enum import Enum
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator, root_validator
import os


# =============================================================================
# Core Enums and Types
# =============================================================================

class EnvironmentType(str, Enum):
    """Deployment environment types"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CI_CD = "ci_cd"
    GITHUB_ACTIONS = "github_actions"


class PipelineStage(str, Enum):
    """5-stage pipeline stages"""
    NOTION_SYNC = "notion_sync"
    CONTENT_PROCESSING = "content_processing"
    HUGO_BUILD = "hugo_build"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class SyncMode(str, Enum):
    """Content synchronization modes"""
    INCREMENTAL = "incremental"
    FULL = "full"
    SMART = "smart"
    FORCE = "force"


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms"""
    GITHUB_PAGES = "github_pages"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    AWS_S3 = "aws_s3"
    CLOUDFLARE_PAGES = "cloudflare_pages"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# Stage 1: Notion Sync Configuration
# =============================================================================

class NotionApiConfig(BaseModel):
    """Notion API connection configuration"""
    token: str = Field(..., description="Notion API token (ntn_...)")
    timeout: int = Field(30, ge=5, le=300, description="API timeout in seconds")
    rate_limit_delay: float = Field(0.1, ge=0.0, le=2.0, description="Delay between API calls")
    max_retries: int = Field(3, ge=1, le=10, description="Maximum retry attempts")
    backoff_factor: float = Field(2.0, ge=1.0, le=5.0, description="Exponential backoff factor")
    
    @validator('token')
    def validate_token(cls, v):
        if not v.startswith('ntn_'):
            raise ValueError('Token must start with "ntn_"')
        if len(v) < 50:
            raise ValueError('Token appears to be too short')
        return v


class NotionDatabaseMount(BaseModel):
    """Notion database mount configuration"""
    database_id: str = Field(..., description="Notion database ID")
    target_folder: str = Field("posts", description="Target content folder")
    content_type: Literal["post", "page"] = Field("post", description="Content type")
    property_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "title": "Name",
            "status": "Status",
            "date": "Date",
            "tags": "Tags",
            "category": "Category"
        },
        description="Property name mapping"
    )
    filters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "status": ["Published", "Live"],
            "archived": False
        },
        description="Database filters"
    )


class NotionPageMount(BaseModel):
    """Notion page mount configuration"""
    page_id: str = Field(..., description="Notion page ID")
    target_file: str = Field(..., description="Target markdown file path")
    content_type: Literal["page", "about", "landing"] = Field("page", description="Page type")


class NotionSyncConfig(BaseModel):
    """Notion synchronization configuration"""
    mode: SyncMode = Field(SyncMode.SMART, description="Synchronization mode")
    batch_size: int = Field(50, ge=1, le=100, description="Batch processing size")
    include_drafts: bool = Field(False, description="Include draft content")
    preserve_notion_ids: bool = Field(True, description="Keep Notion IDs in frontmatter")
    download_images: bool = Field(True, description="Download and store images locally")
    convert_callouts: bool = Field(True, description="Convert Notion callouts to Hugo shortcodes")
    
    # Date range filtering
    date_filter: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Date range filter (from/to)"
    )


class NotionPipelineConfig(BaseModel):
    """Complete Notion pipeline configuration"""
    api: NotionApiConfig
    databases: List[NotionDatabaseMount] = Field(default_factory=list)
    pages: List[NotionPageMount] = Field(default_factory=list)
    sync: NotionSyncConfig = Field(default_factory=NotionSyncConfig)
    
    # Output configuration
    output_dir: str = Field("hugo/content", description="Output directory for markdown files")
    markdown_format: Literal["hugo", "standard"] = Field("hugo", description="Markdown format")
    
    # Performance configuration
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_concurrent_requests: int = Field(5, ge=1, le=20, description="Max concurrent API requests")


# =============================================================================
# Stage 2: Content Processing Configuration
# =============================================================================

class ContentImageConfig(BaseModel):
    """Image processing configuration"""
    optimization_enabled: bool = Field(True, description="Enable image optimization")
    max_width: int = Field(1200, ge=100, le=4000, description="Maximum image width")
    quality: int = Field(85, ge=10, le=100, description="Image quality percentage")
    formats: List[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "webp"],
        description="Supported image formats"
    )
    output_dir: str = Field("hugo/static/images", description="Image output directory")


class ContentValidationConfig(BaseModel):
    """Content validation configuration"""
    required_frontmatter: List[str] = Field(
        default_factory=lambda: ["title", "date"],
        description="Required frontmatter fields"
    )
    validate_markdown_syntax: bool = Field(True, description="Validate Markdown syntax")
    validate_links: bool = Field(True, description="Validate internal/external links")
    max_content_size_mb: int = Field(10, ge=1, le=100, description="Max content size in MB")


class ContentProcessingConfig(BaseModel):
    """Content processing pipeline configuration"""
    images: ContentImageConfig = Field(default_factory=ContentImageConfig)
    validation: ContentValidationConfig = Field(default_factory=ContentValidationConfig)
    
    # Processing options
    enable_toc: bool = Field(True, description="Generate table of contents")
    enable_excerpt: bool = Field(True, description="Generate content excerpts")
    enable_word_count: bool = Field(True, description="Calculate word counts")
    enable_reading_time: bool = Field(True, description="Calculate reading time")
    
    # File handling
    preserve_original: bool = Field(False, description="Keep original Notion markdown")
    backup_enabled: bool = Field(True, description="Create backups during processing")


# =============================================================================
# Stage 3: Hugo Build Configuration
# =============================================================================

class HugoSiteConfig(BaseModel):
    """Hugo site configuration"""
    base_url: str = Field("http://localhost:1313", description="Site base URL")
    title: str = Field("My Blog", description="Site title")
    description: str = Field("A blog powered by Notion and Hugo", description="Site description")
    language: str = Field("en", description="Site language code")
    author: str = Field("", description="Site author")


class HugoThemeConfig(BaseModel):
    """Hugo theme configuration"""
    name: str = Field("PaperMod", description="Theme name")
    version: Optional[str] = Field(None, description="Theme version")
    params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "env": "production",
            "default_theme": "auto",
            "show_reading_time": True,
            "show_share_buttons": True,
            "show_code_copy_buttons": True
        },
        description="Theme parameters"
    )


class HugoBuildConfig(BaseModel):
    """Hugo build configuration"""
    mode: Literal["development", "production"] = Field("production", description="Build mode")
    minify: bool = Field(True, description="Minify output files")
    enable_git_info: bool = Field(True, description="Include Git information")
    build_drafts: bool = Field(False, description="Build draft content")
    build_future: bool = Field(False, description="Build future-dated content")
    build_expired: bool = Field(False, description="Build expired content")
    
    # Performance
    parallel: bool = Field(True, description="Enable parallel processing")
    cache_dir: str = Field("hugo/cache", description="Hugo cache directory")
    timeout: int = Field(60, ge=10, le=600, description="Build timeout in seconds")


class HugoPipelineConfig(BaseModel):
    """Complete Hugo pipeline configuration"""
    # Directory structure
    content_dir: str = Field("hugo/content", description="Content directory")
    static_dir: str = Field("hugo/static", description="Static files directory")
    layouts_dir: str = Field("hugo/layouts", description="Layouts directory")
    output_dir: str = Field("hugo/public", description="Build output directory")
    config_file: str = Field("hugo/config.yaml", description="Hugo config file path")
    
    # Configuration sections
    site: HugoSiteConfig = Field(default_factory=HugoSiteConfig)
    theme: HugoThemeConfig = Field(default_factory=HugoThemeConfig)
    build: HugoBuildConfig = Field(default_factory=HugoBuildConfig)
    
    # Development server
    dev_server: Dict[str, Any] = Field(
        default_factory=lambda: {
            "port": 1313,
            "host": "localhost",
            "watch": True,
            "live_reload": True
        },
        description="Development server configuration"
    )


# =============================================================================
# Stage 4: Deployment Configuration
# =============================================================================

class DeploymentCredentials(BaseModel):
    """Deployment platform credentials"""
    # GitHub Pages
    github_token: Optional[str] = Field(None, description="GitHub Personal Access Token")
    github_repository: Optional[str] = Field(None, description="GitHub repository (owner/repo)")
    
    # Vercel
    vercel_token: Optional[str] = Field(None, description="Vercel API token")
    vercel_project_id: Optional[str] = Field(None, description="Vercel project ID")
    vercel_team_id: Optional[str] = Field(None, description="Vercel team ID")
    
    # Netlify
    netlify_token: Optional[str] = Field(None, description="Netlify API token")
    netlify_site_id: Optional[str] = Field(None, description="Netlify site ID")
    
    # AWS S3
    aws_access_key_id: Optional[str] = Field(None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS secret access key")
    aws_s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    aws_region: Optional[str] = Field(None, description="AWS region")


class DeploymentOptions(BaseModel):
    """Deployment options configuration"""
    auto_deploy: bool = Field(True, description="Enable automatic deployment")
    cache_invalidation: bool = Field(True, description="Invalidate CDN cache")
    compression: bool = Field(True, description="Enable file compression")
    cdn_enabled: bool = Field(True, description="Enable CDN")
    custom_domain: Optional[str] = Field(None, description="Custom domain name")
    
    # GitHub Pages specific
    gh_pages_branch: str = Field("gh-pages", description="GitHub Pages branch")
    force_orphan: bool = Field(True, description="Create orphan gh-pages branch")
    
    # Performance
    parallel_uploads: int = Field(4, ge=1, le=20, description="Parallel upload threads")
    timeout: int = Field(300, ge=60, le=1800, description="Deployment timeout in seconds")
    max_retries: int = Field(3, ge=1, le=10, description="Maximum retry attempts")


class DeploymentPipelineConfig(BaseModel):
    """Complete deployment pipeline configuration"""
    platform: DeploymentPlatform = Field(DeploymentPlatform.GITHUB_PAGES, description="Target platform")
    credentials: DeploymentCredentials = Field(default_factory=DeploymentCredentials)
    options: DeploymentOptions = Field(default_factory=DeploymentOptions)
    
    # Input/Output
    site_directory: str = Field("hugo/public", description="Site directory to deploy")
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [".DS_Store", "*.log", "Thumbs.db", ".git*"],
        description="Files to ignore during deployment"
    )
    
    # Monitoring
    health_check_url: Optional[str] = Field(None, description="Health check endpoint")
    response_timeout: int = Field(30, ge=5, le=120, description="Health check timeout")


# =============================================================================
# Stage 5: Monitoring Configuration
# =============================================================================

class MonitoringAlertsConfig(BaseModel):
    """Monitoring alerts configuration"""
    email_notifications: bool = Field(False, description="Enable email notifications")
    slack_webhook: Optional[str] = Field(None, description="Slack webhook URL")
    discord_webhook: Optional[str] = Field(None, description="Discord webhook URL")
    
    # Alert thresholds
    response_time_threshold: int = Field(5000, description="Response time threshold in ms")
    error_rate_threshold: float = Field(0.05, description="Error rate threshold (0.0-1.0)")


class MonitoringMetricsConfig(BaseModel):
    """Monitoring metrics configuration"""
    collect_performance: bool = Field(True, description="Collect performance metrics")
    collect_uptime: bool = Field(True, description="Monitor site uptime")
    collect_analytics: bool = Field(False, description="Collect analytics data")
    
    # Storage
    metrics_retention_days: int = Field(30, ge=7, le=365, description="Metrics retention period")
    storage_path: str = Field("monitoring/metrics", description="Metrics storage path")


class MonitoringPipelineConfig(BaseModel):
    """Complete monitoring pipeline configuration"""
    enabled: bool = Field(False, description="Enable monitoring pipeline")
    alerts: MonitoringAlertsConfig = Field(default_factory=MonitoringAlertsConfig)
    metrics: MonitoringMetricsConfig = Field(default_factory=MonitoringMetricsConfig)
    
    # Monitoring intervals
    health_check_interval: int = Field(300, ge=60, le=3600, description="Health check interval in seconds")
    metrics_collection_interval: int = Field(900, ge=300, le=7200, description="Metrics collection interval")


# =============================================================================
# Complete Pipeline Configuration
# =============================================================================

class PipelineConfigs(BaseModel):
    """All pipeline stage configurations"""
    notion: NotionPipelineConfig
    content_processing: ContentProcessingConfig = Field(default_factory=ContentProcessingConfig)
    hugo: HugoPipelineConfig = Field(default_factory=HugoPipelineConfig)
    deployment: DeploymentPipelineConfig = Field(default_factory=DeploymentPipelineConfig)
    monitoring: MonitoringPipelineConfig = Field(default_factory=MonitoringPipelineConfig)


# =============================================================================
# Environment and Security Configuration
# =============================================================================

class EnvironmentConfig(BaseModel):
    """Environment-specific configuration"""
    type: EnvironmentType = Field(EnvironmentType.LOCAL, description="Environment type")
    debug_enabled: bool = Field(False, description="Enable debug mode")
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    
    # Environment variables
    use_env_variables: bool = Field(True, description="Use environment variables")
    validate_env_variables: bool = Field(True, description="Validate environment variables")
    required_env_vars: List[str] = Field(
        default_factory=lambda: ["NOTION_TOKEN"],
        description="Required environment variables"
    )


class SecurityConfig(BaseModel):
    """Security configuration"""
    mask_sensitive_logs: bool = Field(True, description="Mask sensitive information in logs")
    token_validation: bool = Field(True, description="Validate API tokens")
    backup_config: bool = Field(True, description="Backup configuration files")
    
    # Patterns to mask in logs
    mask_patterns: List[str] = Field(
        default_factory=lambda: [
            r"ntn_[a-zA-Z0-9]+",  # Notion tokens
            r"ghp_[a-zA-Z0-9]+",  # GitHub tokens
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"  # UUIDs
        ],
        description="Regex patterns for sensitive data"
    )


# =============================================================================
# Complete Configuration Schema
# =============================================================================

class PipelineConfig(BaseModel):
    """Complete Notion-Hugo pipeline configuration"""
    # Metadata
    config_version: str = Field("2.0.0", description="Configuration schema version")
    generated_at: datetime = Field(default_factory=datetime.now, description="Configuration generation time")
    last_updated: Optional[datetime] = Field(None, description="Last update time")
    
    # Core configuration sections
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    pipelines: PipelineConfigs
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "experimental_ui": False,
            "advanced_caching": False,
            "plugin_system": False,
            "legacy_support": True
        },
        description="Feature flags"
    )
    
    @root_validator
    def validate_configuration(cls, values):
        """Validate cross-section configuration dependencies"""
        pipelines = values.get('pipelines')
        if not pipelines:
            return values
            
        # Validate that notion databases are configured if deployment is enabled
        if pipelines.deployment.options.auto_deploy:
            if not pipelines.notion.databases and not pipelines.notion.pages:
                raise ValueError("At least one Notion database or page must be configured for auto-deployment")
        
        # Validate deployment credentials based on platform
        platform = pipelines.deployment.platform
        credentials = pipelines.deployment.credentials
        
        if platform == DeploymentPlatform.GITHUB_PAGES:
            if not credentials.github_token or not credentials.github_repository:
                raise ValueError("GitHub token and repository are required for GitHub Pages deployment")
        elif platform == DeploymentPlatform.VERCEL:
            if not credentials.vercel_token:
                raise ValueError("Vercel token is required for Vercel deployment")
        elif platform == DeploymentPlatform.NETLIFY:
            if not credentials.netlify_token or not credentials.netlify_site_id:
                raise ValueError("Netlify token and site ID are required for Netlify deployment")
        
        return values


# =============================================================================
# Legacy Configuration Support (TypedDict for backward compatibility)
# =============================================================================

class LegacyDatabaseMount(TypedDict):
    """Legacy database mount structure"""
    database_id: str
    target_folder: str


class LegacyPageMount(TypedDict):
    """Legacy page mount structure"""
    page_id: str
    target_folder: str


class LegacyMount(TypedDict):
    """Legacy mount structure"""
    databases: List[LegacyDatabaseMount]
    pages: List[LegacyPageMount]


class LegacyFilenameConfig(TypedDict):
    """Legacy filename configuration"""
    format: str
    date_format: str
    korean_title: str


class LegacyDeploymentConfig(TypedDict):
    """Legacy deployment configuration"""
    auto_deploy: bool
    trigger: str
    schedule: Optional[str]
    environment: str


class LegacySecurityConfig(TypedDict):
    """Legacy security configuration"""
    use_environment_variables: bool
    mask_sensitive_logs: bool
    token_validation: bool


class LegacyConfig(TypedDict):
    """Complete legacy configuration structure"""
    mount: LegacyMount
    filename: Optional[LegacyFilenameConfig]
    deployment: Optional[LegacyDeploymentConfig]
    security: Optional[LegacySecurityConfig]


# =============================================================================
# Configuration Factory and Utilities
# =============================================================================

def create_default_config() -> PipelineConfig:
    """Create a default pipeline configuration"""
    return PipelineConfig(
        pipelines=PipelineConfigs(
            notion=NotionPipelineConfig(
                api=NotionApiConfig(
                    token="${NOTION_TOKEN}"
                )
            )
        )
    )


def create_development_config() -> PipelineConfig:
    """Create a development-optimized configuration"""
    config = create_default_config()
    config.environment.type = EnvironmentType.DEVELOPMENT
    config.environment.debug_enabled = True
    config.environment.log_level = LogLevel.DEBUG
    config.pipelines.hugo.build.mode = "development"
    config.pipelines.hugo.build.minify = False
    config.pipelines.deployment.options.auto_deploy = False
    return config


def create_production_config() -> PipelineConfig:
    """Create a production-optimized configuration"""
    config = create_default_config()
    config.environment.type = EnvironmentType.PRODUCTION
    config.environment.debug_enabled = False
    config.environment.log_level = LogLevel.INFO
    config.pipelines.hugo.build.mode = "production"
    config.pipelines.hugo.build.minify = True
    config.pipelines.deployment.options.auto_deploy = True
    config.pipelines.monitoring.enabled = True
    return config


# Export all configuration types
__all__ = [
    # Main configuration
    'PipelineConfig',
    'PipelineConfigs',
    
    # Pipeline stage configs
    'NotionPipelineConfig',
    'ContentProcessingConfig', 
    'HugoPipelineConfig',
    'DeploymentPipelineConfig',
    'MonitoringPipelineConfig',
    
    # Support configs
    'EnvironmentConfig',
    'SecurityConfig',
    
    # Enums
    'EnvironmentType',
    'PipelineStage',
    'SyncMode',
    'DeploymentPlatform',
    'LogLevel',
    
    # Legacy support
    'LegacyConfig',
    'LegacyMount',
    'LegacyDatabaseMount',
    'LegacyPageMount',
    
    # Factory functions
    'create_default_config',
    'create_development_config',
    'create_production_config',
]