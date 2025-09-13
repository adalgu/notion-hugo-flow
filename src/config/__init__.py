"""
Configuration Management System for Notion-Hugo Pipeline

Provides unified configuration management for the entire 5-stage pipeline with:
- Environment variable mapping and backward compatibility 
- Comprehensive validation for all pipeline stages
- Smart deployment environment detection
- Production-ready error handling and reporting
"""

from .config import Config, ConfigManager, load_config, create_config_file, DatabaseMount, PageMount, FilenameConfig, diagnose_configuration
from .smart_config import SmartConfigManager, ThemeManager
from .env_mapper import EnvironmentVariableMapper, get_env, validate_required_env, create_env_template
from .unified_config import (
    UnifiedConfigLoader, 
    PipelineValidationError,
    load_pipeline_config,
    validate_pipeline,
    is_deployment_ready,
    get_configuration_report
)

__all__ = [
    # Legacy configuration system (backward compatibility)
    "Config", 
    "ConfigManager",
    "load_config", 
    "create_config_file", 
    "DatabaseMount", 
    "PageMount",
    "FilenameConfig",
    "diagnose_configuration",
    
    # Smart configuration system
    "SmartConfigManager",
    "ThemeManager",
    
    # Environment variable mapping
    "EnvironmentVariableMapper",
    "get_env",
    "validate_required_env", 
    "create_env_template",
    
    # Unified configuration system (recommended)
    "UnifiedConfigLoader",
    "PipelineValidationError",
    "load_pipeline_config",
    "validate_pipeline",
    "is_deployment_ready",
    "get_configuration_report"
]