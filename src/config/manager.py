#!/usr/bin/env python3
"""
Configuration Manager for Notion-Hugo Phase 2 Pipeline

This module provides comprehensive configuration management including:
- Pydantic-based validation and type checking  
- Environment variable mapping with intelligent overrides
- Legacy configuration migration and compatibility
- Multi-environment support (local, staging, production, CI/CD)
- Configuration health checks and dependency validation
- Hot-reloading and dynamic configuration updates

Usage:
    from src.config.manager import ConfigurationManager
    
    # Initialize with automatic environment detection
    config_manager = ConfigurationManager()
    
    # Load and validate configuration
    config = config_manager.load_validated_config()
    
    # Access typed configuration sections
    notion_config = config.pipelines.notion
    deployment_config = config.pipelines.deployment
    
    # Perform health checks
    health_status = config_manager.validate_health()
"""

import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Type, Callable
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager

import pydantic
from pydantic import ValidationError

from .schema import (
    PipelineConfig,
    EnvironmentType,
    DeploymentPlatform,
    SyncMode,
    LogLevel,
    LegacyConfig,
    create_default_config,
    create_development_config,
    create_production_config,
)


# =============================================================================
# Configuration Loading and Validation
# =============================================================================

@dataclass
class ConfigurationSource:
    """Configuration source information"""
    path: str
    exists: bool
    format: str  # yaml, json, env
    priority: int  # Higher number = higher priority
    last_modified: Optional[datetime] = None


@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    config: Optional[PipelineConfig] = None


@dataclass
class HealthCheckResult:
    """System health check result"""
    overall_healthy: bool
    stage_health: Dict[str, bool]
    missing_dependencies: List[str]
    configuration_issues: List[str]
    recommendations: List[str]


class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass


class EnvironmentDetector:
    """Detects the current deployment environment"""
    
    @staticmethod
    def detect_environment() -> EnvironmentType:
        """Detect current environment from system indicators"""
        # CI/CD environments
        if os.getenv('GITHUB_ACTIONS'):
            return EnvironmentType.GITHUB_ACTIONS
        elif os.getenv('CI'):
            return EnvironmentType.CI_CD
        
        # Cloud platforms
        elif os.getenv('VERCEL'):
            return EnvironmentType.PRODUCTION
        elif os.getenv('NETLIFY'):
            return EnvironmentType.PRODUCTION
            
        # Environment variables
        env_type = os.getenv('ENVIRONMENT', '').lower()
        if env_type in ['prod', 'production']:
            return EnvironmentType.PRODUCTION
        elif env_type in ['stage', 'staging']:
            return EnvironmentType.STAGING
        elif env_type in ['dev', 'development']:
            return EnvironmentType.DEVELOPMENT
        
        # Default to local
        return EnvironmentType.LOCAL
    
    @staticmethod
    def is_ci_environment() -> bool:
        """Check if running in CI environment"""
        ci_indicators = [
            'CI', 'CONTINUOUS_INTEGRATION', 
            'GITHUB_ACTIONS', 'GITLAB_CI', 
            'JENKINS_URL', 'TRAVIS', 'CIRCLECI'
        ]
        return any(os.getenv(var) for var in ci_indicators)


class EnvironmentVariableResolver:
    """Resolves environment variables in configuration"""
    
    # Pattern for environment variable substitution: ${VAR_NAME} or ${VAR_NAME:-default}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    @classmethod
    def resolve_string(cls, value: str) -> str:
        """Resolve environment variables in a string"""
        if not isinstance(value, str):
            return value
            
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.getenv(var_name.strip(), default_value)
            else:
                var_name = var_expr.strip()
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ConfigurationError(f"Required environment variable '{var_name}' is not set")
                return env_value
        
        return cls.ENV_VAR_PATTERN.sub(replace_env_var, value)
    
    @classmethod
    def resolve_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve environment variables in a dictionary"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = cls.resolve_string(value)
            elif isinstance(value, dict):
                result[key] = cls.resolve_dict(value)
            elif isinstance(value, list):
                result[key] = cls.resolve_list(value)
            else:
                result[key] = value
        return result
    
    @classmethod
    def resolve_list(cls, data: List[Any]) -> List[Any]:
        """Recursively resolve environment variables in a list"""
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(cls.resolve_string(item))
            elif isinstance(item, dict):
                result.append(cls.resolve_dict(item))
            elif isinstance(item, list):
                result.append(cls.resolve_list(item))
            else:
                result.append(item)
        return result


class EnvironmentVariableOverride:
    """Handles environment variable overrides using dot notation"""
    
    @staticmethod
    def apply_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Pattern: SECTION_SUBSECTION_KEY -> section.subsection.key
        for env_key, env_value in os.environ.items():
            if not env_value:  # Skip empty values
                continue
                
            # Convert UPPER_CASE_WITH_UNDERSCORES to lowercase.dot.notation
            config_path = env_key.lower().replace('_', '.')
            path_parts = config_path.split('.')
            
            # Only process if it looks like a config path (at least 2 parts)
            if len(path_parts) < 2:
                continue
                
            try:
                # Navigate to the parent dict and set the value
                current = config_dict
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set the final value with type conversion
                final_key = path_parts[-1]
                current[final_key] = EnvironmentVariableOverride._convert_env_value(env_value)
                
            except (KeyError, TypeError):
                # Skip invalid paths
                continue
                
        return config_dict
    
    @staticmethod
    def _convert_env_value(value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate Python type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)
        
        # Float conversion
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value


class LegacyConfigurationMigrator:
    """Migrates legacy configuration to new schema"""
    
    @staticmethod
    def migrate_from_legacy(legacy_config: LegacyConfig) -> Dict[str, Any]:
        """Convert legacy configuration to new schema format"""
        migrated = {
            'config_version': '2.0.0',
            'generated_at': datetime.now().isoformat(),
            'pipelines': {
                'notion': {
                    'api': {
                        'token': '${NOTION_TOKEN}',
                        'timeout': 30,
                        'rate_limit_delay': 0.1,
                        'max_retries': 3,
                        'backoff_factor': 2.0
                    },
                    'databases': [],
                    'pages': [],
                    'sync': {
                        'mode': 'smart',
                        'batch_size': 50,
                        'include_drafts': False,
                        'preserve_notion_ids': True,
                        'download_images': True,
                        'convert_callouts': True
                    },
                    'output_dir': 'hugo/content',
                    'markdown_format': 'hugo'
                }
            }
        }
        
        # Migrate mount configuration
        if 'mount' in legacy_config:
            mount = legacy_config['mount']
            
            # Migrate databases
            for db in mount.get('databases', []):
                migrated['pipelines']['notion']['databases'].append({
                    'database_id': db['database_id'],
                    'target_folder': db['target_folder'],
                    'content_type': 'post',
                    'property_mapping': {
                        'title': 'Name',
                        'status': 'Status',
                        'date': 'Date',
                        'tags': 'Tags',
                        'category': 'Category'
                    },
                    'filters': {
                        'status': ['Published', 'Live'],
                        'archived': False
                    }
                })
            
            # Migrate pages
            for page in mount.get('pages', []):
                migrated['pipelines']['notion']['pages'].append({
                    'page_id': page['page_id'],
                    'target_file': page.get('target_folder', 'content/page.md'),
                    'content_type': 'page'
                })
        
        # Add other pipeline configurations with defaults
        migrated['pipelines'].update({
            'content_processing': {
                'images': {
                    'optimization_enabled': True,
                    'max_width': 1200,
                    'quality': 85,
                    'formats': ['jpg', 'jpeg', 'png', 'webp']
                },
                'validation': {
                    'required_frontmatter': ['title', 'date'],
                    'validate_markdown_syntax': True,
                    'validate_links': True
                }
            },
            'hugo': {
                'content_dir': 'hugo/content',
                'static_dir': 'hugo/static', 
                'output_dir': 'hugo/public',
                'config_file': 'hugo/config.yaml',
                'site': {
                    'base_url': 'http://localhost:1313',
                    'title': 'My Blog',
                    'description': 'A blog powered by Notion and Hugo',
                    'language': 'en',
                    'author': ''
                },
                'theme': {
                    'name': 'PaperMod',
                    'params': {
                        'env': 'production',
                        'default_theme': 'auto',
                        'show_reading_time': True
                    }
                },
                'build': {
                    'mode': 'production',
                    'minify': True,
                    'enable_git_info': True,
                    'build_drafts': False
                }
            },
            'deployment': {
                'platform': 'github_pages',
                'credentials': {
                    'github_token': '${GITHUB_TOKEN}',
                    'github_repository': '${GITHUB_REPOSITORY}'
                },
                'options': {
                    'auto_deploy': True,
                    'cache_invalidation': True,
                    'compression': True
                }
            },
            'monitoring': {
                'enabled': False,
                'alerts': {
                    'email_notifications': False
                },
                'metrics': {
                    'collect_performance': True,
                    'collect_uptime': True
                }
            }
        })
        
        # Migrate security settings
        if 'security' in legacy_config:
            security = legacy_config['security']
            migrated['security'] = {
                'mask_sensitive_logs': security.get('mask_sensitive_logs', True),
                'token_validation': security.get('token_validation', True),
                'backup_config': True
            }
        
        return migrated
    
    @staticmethod
    def detect_legacy_config(config_dict: Dict[str, Any]) -> bool:
        """Detect if configuration uses legacy format"""
        legacy_indicators = ['mount', 'filename']
        return any(key in config_dict for key in legacy_indicators)


# =============================================================================
# Main Configuration Manager
# =============================================================================

class ConfigurationManager:
    """Comprehensive configuration management for Notion-Hugo pipeline"""
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 auto_detect_environment: bool = True,
                 enable_hot_reload: bool = False):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (auto-detected if None)
            auto_detect_environment: Automatically detect deployment environment
            enable_hot_reload: Enable configuration hot-reloading
        """
        self.config_path = config_path
        self.auto_detect_environment = auto_detect_environment
        self.enable_hot_reload = enable_hot_reload
        
        # Current environment
        self.environment = EnvironmentDetector.detect_environment() if auto_detect_environment else EnvironmentType.LOCAL
        
        # Configuration cache
        self._config_cache: Optional[PipelineConfig] = None
        self._cache_timestamp: Optional[datetime] = None
        
        # Configuration sources
        self._config_sources: List[ConfigurationSource] = []
        self._discover_config_sources()
    
    def _discover_config_sources(self) -> None:
        """Discover available configuration sources"""
        base_paths = [
            Path.cwd(),
            Path.cwd() / "src" / "config",
            Path.cwd() / "config",
            Path(__file__).parent,
        ]
        
        config_files = [
            "notion-hugo-config.yaml",
            "config.yaml", 
            "pipeline.yaml",
            "notion-hugo.config.yaml",
            "config.yml"
        ]
        
        self._config_sources = []
        
        for priority, base_path in enumerate(base_paths, 1):
            for filename in config_files:
                file_path = base_path / filename
                if file_path.exists():
                    self._config_sources.append(ConfigurationSource(
                        path=str(file_path),
                        exists=True,
                        format="yaml",
                        priority=priority,
                        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
                    ))
        
        # Sort by priority (higher priority first)
        self._config_sources.sort(key=lambda x: x.priority, reverse=True)
    
    def load_validated_config(self, force_reload: bool = False) -> PipelineConfig:
        """Load and validate configuration with caching
        
        Args:
            force_reload: Force reload even if cached version exists
            
        Returns:
            Validated pipeline configuration
            
        Raises:
            ConfigurationError: If configuration is invalid or cannot be loaded
        """
        # Check cache validity
        if not force_reload and self._is_cache_valid():
            return self._config_cache
        
        # Load raw configuration
        raw_config = self._load_raw_config()
        
        # Validate and create PipelineConfig object
        validation_result = self._validate_config(raw_config)
        
        if not validation_result.is_valid:
            error_msg = f"Configuration validation failed:\n" + "\n".join(validation_result.errors)
            raise ConfigurationError(error_msg)
        
        # Cache the validated configuration
        self._config_cache = validation_result.config
        self._cache_timestamp = datetime.now()
        
        return self._config_cache
    
    def _is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid"""
        if not self._config_cache or not self._cache_timestamp:
            return False
        
        # If hot reload is disabled, cache is always valid
        if not self.enable_hot_reload:
            return True
        
        # Check if any source files have been modified
        for source in self._config_sources:
            if source.exists:
                file_path = Path(source.path)
                if file_path.exists():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime > self._cache_timestamp:
                        return False
        
        return True
    
    def _load_raw_config(self) -> Dict[str, Any]:
        """Load raw configuration from available sources"""
        if self.config_path:
            # Load from specific path
            return self._load_config_file(self.config_path)
        
        # Load from discovered sources (highest priority first)
        for source in self._config_sources:
            if source.exists:
                try:
                    config_data = self._load_config_file(source.path)
                    if config_data:  # Non-empty configuration found
                        return config_data
                except Exception as e:
                    # Log warning and continue to next source
                    print(f"Warning: Failed to load config from {source.path}: {e}")
                    continue
        
        # No configuration found - return default
        return self._create_default_raw_config()
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from a specific file"""
        path = Path(file_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yml', '.yaml']:
                    raw_data = yaml.safe_load(f) or {}
                elif path.suffix.lower() == '.json':
                    raw_data = json.load(f) or {}
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration file {file_path}: {e}")
        
        # Resolve environment variables
        try:
            resolved_data = EnvironmentVariableResolver.resolve_dict(raw_data)
        except ConfigurationError:
            # If required env vars are missing, we'll catch this in validation
            resolved_data = raw_data
        
        # Apply environment variable overrides
        overridden_data = EnvironmentVariableOverride.apply_overrides(resolved_data)
        
        # Handle legacy configuration migration
        if LegacyConfigurationMigrator.detect_legacy_config(overridden_data):
            print("Legacy configuration detected - migrating to new format")
            overridden_data = LegacyConfigurationMigrator.migrate_from_legacy(overridden_data)
        
        return overridden_data
    
    def _create_default_raw_config(self) -> Dict[str, Any]:
        """Create default raw configuration based on environment"""
        if self.environment == EnvironmentType.DEVELOPMENT:
            default_config = create_development_config()
        elif self.environment == EnvironmentType.PRODUCTION:
            default_config = create_production_config()
        else:
            default_config = create_default_config()
        
        # Convert to dict for processing
        return default_config.dict()
    
    def _validate_config(self, config_dict: Dict[str, Any]) -> ValidationResult:
        """Validate configuration dictionary against Pydantic schema"""
        errors = []
        warnings = []
        config = None
        
        try:
            # Create PipelineConfig from dictionary
            config = PipelineConfig(**config_dict)
            
            # Additional validation checks
            validation_warnings = self._perform_additional_validation(config)
            warnings.extend(validation_warnings)
            
        except ValidationError as e:
            # Convert Pydantic validation errors to readable format
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                error_msg = f"{field_path}: {error['msg']}"
                errors.append(error_msg)
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            config=config
        )
    
    def _perform_additional_validation(self, config: PipelineConfig) -> List[str]:
        """Perform additional validation beyond Pydantic schema"""
        warnings = []
        
        # Check for common configuration issues
        notion_config = config.pipelines.notion
        
        # Warn if no databases or pages configured
        if not notion_config.databases and not notion_config.pages:
            warnings.append("No Notion databases or pages configured - sync will have nothing to process")
        
        # Warn if API token looks like a placeholder
        if notion_config.api.token.startswith('${') or notion_config.api.token == 'your_token_here':
            warnings.append("Notion API token appears to be a placeholder - please set NOTION_TOKEN environment variable")
        
        # Check deployment configuration
        deployment_config = config.pipelines.deployment
        if deployment_config.options.auto_deploy:
            platform = deployment_config.platform
            credentials = deployment_config.credentials
            
            if platform.value == 'github_pages':
                if not credentials.github_token or credentials.github_token.startswith('${'):
                    warnings.append("GitHub Pages deployment enabled but no GitHub token configured")
                if not credentials.github_repository or credentials.github_repository.startswith('${'):
                    warnings.append("GitHub Pages deployment enabled but no repository configured")
        
        return warnings
    
    # =============================================================================
    # Health Checks and Dependency Validation
    # =============================================================================
    
    def validate_health(self) -> HealthCheckResult:
        """Perform comprehensive system health check"""
        try:
            config = self.load_validated_config()
        except ConfigurationError as e:
            return HealthCheckResult(
                overall_healthy=False,
                stage_health={},
                missing_dependencies=[],
                configuration_issues=[str(e)],
                recommendations=["Fix configuration errors before proceeding"]
            )
        
        stage_health = {}
        missing_dependencies = []
        configuration_issues = []
        recommendations = []
        
        # Check each pipeline stage
        stage_health['notion'] = self._check_notion_health(config, missing_dependencies, configuration_issues, recommendations)
        stage_health['hugo'] = self._check_hugo_health(config, missing_dependencies, configuration_issues, recommendations)
        stage_health['deployment'] = self._check_deployment_health(config, missing_dependencies, configuration_issues, recommendations)
        
        overall_healthy = all(stage_health.values()) and len(configuration_issues) == 0
        
        return HealthCheckResult(
            overall_healthy=overall_healthy,
            stage_health=stage_health,
            missing_dependencies=missing_dependencies,
            configuration_issues=configuration_issues,
            recommendations=recommendations
        )
    
    def _check_notion_health(self, config: PipelineConfig, missing_deps: List[str], issues: List[str], recommendations: List[str]) -> bool:
        """Check Notion pipeline health"""
        notion_config = config.pipelines.notion
        healthy = True
        
        # Check API token
        if not os.getenv('NOTION_TOKEN'):
            missing_deps.append('NOTION_TOKEN environment variable')
            healthy = False
            recommendations.append('Set NOTION_TOKEN environment variable with your Notion API token')
        
        # Check if Notion client can be imported
        try:
            import notion_client
        except ImportError:
            missing_deps.append('notion-client package')
            healthy = False
            recommendations.append('Install notion-client: pip install notion-client')
        
        # Check database/page configuration
        if not notion_config.databases and not notion_config.pages:
            issues.append('No Notion databases or pages configured')
            healthy = False
            recommendations.append('Configure at least one Notion database or page in the configuration')
        
        # Check output directory
        output_path = Path(notion_config.output_dir)
        if not output_path.parent.exists():
            issues.append(f'Output directory parent does not exist: {output_path.parent}')
            recommendations.append(f'Create directory: {output_path.parent}')
        
        return healthy
    
    def _check_hugo_health(self, config: PipelineConfig, missing_deps: List[str], issues: List[str], recommendations: List[str]) -> bool:
        """Check Hugo pipeline health"""
        hugo_config = config.pipelines.hugo
        healthy = True
        
        # Check Hugo installation
        import shutil
        if not shutil.which('hugo'):
            missing_deps.append('Hugo static site generator')
            healthy = False
            recommendations.append('Install Hugo: https://gohugo.io/getting-started/installing/')
        
        # Check theme
        theme_path = Path(f"{hugo_config.content_dir}/../themes/{hugo_config.theme.name}")
        if not theme_path.exists():
            issues.append(f'Hugo theme not found: {theme_path}')
            recommendations.append(f'Install {hugo_config.theme.name} theme or update theme configuration')
        
        # Check content directory
        content_path = Path(hugo_config.content_dir)
        if not content_path.exists():
            issues.append(f'Hugo content directory does not exist: {content_path}')
            recommendations.append(f'Create content directory: {content_path}')
        
        return healthy
    
    def _check_deployment_health(self, config: PipelineConfig, missing_deps: List[str], issues: List[str], recommendations: List[str]) -> bool:
        """Check deployment pipeline health"""
        deployment_config = config.pipelines.deployment
        healthy = True
        
        if not deployment_config.options.auto_deploy:
            return True  # Skip checks if deployment disabled
        
        platform = deployment_config.platform
        credentials = deployment_config.credentials
        
        if platform == DeploymentPlatform.GITHUB_PAGES:
            if not credentials.github_token or not os.getenv('GITHUB_TOKEN'):
                missing_deps.append('GITHUB_TOKEN environment variable')
                healthy = False
                recommendations.append('Set GITHUB_TOKEN environment variable for GitHub Pages deployment')
            
            if not credentials.github_repository or not os.getenv('GITHUB_REPOSITORY'):
                missing_deps.append('GITHUB_REPOSITORY environment variable')
                healthy = False
                recommendations.append('Set GITHUB_REPOSITORY environment variable (format: owner/repo)')
        
        # Check site directory
        site_path = Path(deployment_config.site_directory)
        if not site_path.exists():
            issues.append(f'Site directory does not exist: {site_path}')
            recommendations.append('Run Hugo build before deployment')
        
        return healthy
    
    # =============================================================================
    # Configuration Management Utilities
    # =============================================================================
    
    def save_config(self, config: PipelineConfig, file_path: Optional[str] = None) -> None:
        """Save configuration to file"""
        if file_path is None:
            if self._config_sources:
                file_path = self._config_sources[0].path
            else:
                file_path = "src/config/notion-hugo-config.yaml"
        
        # Convert to dict and resolve any remaining variables
        config_dict = config.dict()
        
        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save as YAML
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def create_environment_template(self, file_path: str = ".env.template") -> None:
        """Create environment variable template file"""
        template_content = f"""# Notion-Hugo Pipeline Environment Variables
# Copy this file to .env and fill in your values

# === REQUIRED ===
# Notion API Token (get from https://www.notion.so/my-integrations)
NOTION_TOKEN=ntn_your_token_here

# === DEPLOYMENT (GitHub Pages) ===
# GitHub Personal Access Token (for deployment)
GITHUB_TOKEN=ghp_your_token_here
# Repository in format: username/repo-name  
GITHUB_REPOSITORY=username/repo-name

# === OPTIONAL ===
# Environment type (local|development|staging|production)
ENVIRONMENT={self.environment.value}

# Site configuration
HUGO_SITE_BASE_URL=https://yourdomain.com
HUGO_SITE_TITLE=Your Blog Title
HUGO_SITE_DESCRIPTION=Your blog description
HUGO_SITE_AUTHOR=Your Name

# Build configuration
HUGO_BUILD_MINIFY=true
HUGO_BUILD_ENABLE_GIT_INFO=true

# Deployment options
DEPLOYMENT_OPTIONS_AUTO_DEPLOY=true
DEPLOYMENT_OPTIONS_CACHE_INVALIDATION=true

# Security settings
SECURITY_MASK_SENSITIVE_LOGS=true
SECURITY_TOKEN_VALIDATION=true

# Monitoring (optional)
MONITORING_ENABLED=false
MONITORING_ALERTS_SLACK_WEBHOOK=https://hooks.slack.com/your/webhook/url
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"Environment template created: {file_path}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        try:
            config = self.load_validated_config()
            
            return {
                'config_version': config.config_version,
                'environment': self.environment.value,
                'config_sources': [s.path for s in self._config_sources],
                'primary_config_path': self._config_sources[0].path if self._config_sources else None,
                'cache_valid': self._is_cache_valid(),
                'last_loaded': self._cache_timestamp.isoformat() if self._cache_timestamp else None,
                'pipelines_configured': {
                    'notion': len(config.pipelines.notion.databases) > 0 or len(config.pipelines.notion.pages) > 0,
                    'hugo': bool(config.pipelines.hugo.theme.name),
                    'deployment': config.pipelines.deployment.options.auto_deploy,
                    'monitoring': config.pipelines.monitoring.enabled
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'environment': self.environment.value,
                'config_sources': [s.path for s in self._config_sources]
            }
    
    @contextmanager
    def temporary_config_override(self, overrides: Dict[str, Any]):
        """Temporarily override configuration values"""
        original_config = self._config_cache
        try:
            # Apply overrides to current config
            if original_config:
                config_dict = original_config.dict()
                # Deep merge overrides
                self._deep_update(config_dict, overrides)
                self._config_cache = PipelineConfig(**config_dict)
            yield
        finally:
            # Restore original config
            self._config_cache = original_config
    
    @staticmethod
    def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Deep update dictionary with another dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                ConfigurationManager._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


# =============================================================================
# Convenience Functions
# =============================================================================

def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """Convenience function to load configuration"""
    manager = ConfigurationManager(config_path=config_path)
    return manager.load_validated_config()


def validate_system_health() -> HealthCheckResult:
    """Convenience function to validate system health"""
    manager = ConfigurationManager()
    return manager.validate_health()


def create_config_template(template_type: str = "default") -> PipelineConfig:
    """Create configuration template"""
    if template_type == "development":
        return create_development_config()
    elif template_type == "production":
        return create_production_config()
    else:
        return create_default_config()


# Export main classes and functions
__all__ = [
    'ConfigurationManager',
    'ValidationResult', 
    'HealthCheckResult',
    'ConfigurationError',
    'EnvironmentDetector',
    'load_config',
    'validate_system_health',
    'create_config_template'
]