#!/usr/bin/env python3
"""
Unified Configuration Loader for Notion-Hugo CLI

This module provides a unified configuration system that:
1. Integrates ConfigManager and SmartConfigManager
2. Supports simplified environment variable names
3. Provides comprehensive validation for 5-stage pipeline
4. Maintains backward compatibility with legacy configurations
5. Offers production-ready error handling and validation

Usage:
    from src.config.unified_config import UnifiedConfigLoader
    
    config_loader = UnifiedConfigLoader()
    config = config_loader.load_complete_config()
    
    # Access pipeline stage configurations
    notion_config = config_loader.get_notion_config()
    hugo_config = config_loader.get_hugo_config()
"""

import os
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

from .config import ConfigManager
from .smart_config import SmartConfigManager
from .env_mapper import EnvironmentVariableMapper, get_env


class PipelineValidationError(Exception):
    """Raised when pipeline configuration validation fails."""
    pass


class UnifiedConfigLoader:
    """
    Unified configuration loader that integrates all configuration systems
    and provides comprehensive validation for the 5-stage pipeline.
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 enable_deprecation_warnings: bool = True,
                 project_root: Optional[Path] = None):
        """
        Initialize the unified configuration loader.
        
        Args:
            config_path: Path to configuration file (optional)
            enable_deprecation_warnings: Show warnings for legacy env vars
            project_root: Project root directory (defaults to current working directory)
        """
        self.project_root = project_root or Path.cwd()
        self.config_manager = ConfigManager(config_path)
        self.smart_config_manager = SmartConfigManager(self.project_root)
        self.env_mapper = EnvironmentVariableMapper(enable_deprecation_warnings)
        
        # Pipeline stage configurations
        self._pipeline_config: Optional[Dict[str, Any]] = None
        self._validation_results: Optional[Dict[str, Any]] = None
    
    def load_complete_config(self) -> Dict[str, Any]:
        """
        Load complete configuration combining all sources.
        
        Returns:
            Complete configuration dictionary with all pipeline stage settings
        """
        if self._pipeline_config is None:
            self._pipeline_config = self._build_complete_config()
        
        return self._pipeline_config
    
    def _build_complete_config(self) -> Dict[str, Any]:
        """Build the complete configuration from all sources."""
        
        # Start with base configuration from ConfigManager
        base_config = self.config_manager.load_config()
        
        # Get smart configuration for deployment environment
        environment = self.smart_config_manager.detect_environment()
        deployment_target = self._determine_deployment_target(environment)
        
        # Generate optimized Hugo configuration
        hugo_config = self.smart_config_manager.generate_hugo_config(deployment_target)
        
        # Build unified configuration
        unified_config = {
            "pipeline": {
                "environment": environment,
                "deployment_target": deployment_target,
                "stages": {
                    "notion": self._build_notion_stage_config(base_config),
                    "process": self._build_process_stage_config(base_config),
                    "integrate": self._build_integrate_stage_config(base_config),
                    "build": self._build_build_stage_config(base_config, hugo_config),
                    "deploy": self._build_deploy_stage_config(base_config, environment)
                }
            },
            "base": base_config,
            "hugo": hugo_config,
            "environment": self.env_mapper.get_all_mapped_values(),
            "github": self.smart_config_manager.get_github_info(),
            "paths": self._build_paths_config()
        }
        
        return unified_config
    
    def _determine_deployment_target(self, environment: str) -> str:
        """Determine the deployment target based on environment."""
        if environment == "github_actions":
            return "github"
        elif environment == "vercel":
            return "vercel"
        elif environment == "netlify":
            return "netlify"
        else:
            # Use environment variable or default to github
            return get_env("DEPLOYMENT_TARGET", "github")
    
    def _build_notion_stage_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build configuration for Stage 1: Notion sync."""
        return {
            "token": get_env("NOTION_TOKEN"),
            "database_id": get_env("NOTION_DATABASE_ID"),
            "page_id": get_env("NOTION_PAGE_ID"),
            "output_dir": get_env("NOTION_OUTPUT_DIR", "notion_markdown"),
            "state_file": get_env("STATE_FILE", "src/config/.notion-hugo-state.json"),
            "timeout": int(get_env("NOTION_TIMEOUT", "30")),
            "batch_size": int(get_env("NOTION_BATCH_SIZE", "10")),
            "include_drafts": get_env("INCLUDE_DRAFTS", "false").lower() == "true",
            "sync_mode": get_env("SYNC_MODE", "incremental"),
            "base_config": base_config.get("notion", {})
        }
    
    def _build_process_stage_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build configuration for Stage 2: Content processing."""
        return {
            "input_dir": get_env("PROCESS_INPUT_DIR", "notion_markdown"),
            "output_dir": get_env("PROCESS_OUTPUT_DIR", "hugo_markdown"),
            "enable_optimization": get_env("ENABLE_OPTIMIZATION", "true").lower() == "true",
            "image_processing": get_env("IMAGE_PROCESSING", "true").lower() == "true",
            "base_config": base_config.get("content", {})
        }
    
    def _build_integrate_stage_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build configuration for Stage 3: Hugo integration."""
        return {
            "input_dir": get_env("INTEGRATE_INPUT_DIR", "hugo_markdown"),
            "output_dir": get_env("INTEGRATE_OUTPUT_DIR", "hugo/content"),
            "hugo_content_dir": self.config_manager.get_hugo_content_path(),
            "backup_existing": get_env("BACKUP_EXISTING", "true").lower() == "true",
            "base_config": base_config.get("hugo", {})
        }
    
    def _build_build_stage_config(self, base_config: Dict[str, Any], hugo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build configuration for Stage 4: Hugo build."""
        return {
            "source_dir": get_env("BUILD_SOURCE_DIR", "hugo"),
            "output_dir": get_env("BUILD_OUTPUT_DIR", "hugo/public"),
            "hugo_version": get_env("HUGO_VERSION", "0.140.0"),
            "hugo_extended": get_env("HUGO_EXTENDED", "true").lower() == "true",
            "minify": get_env("BUILD_MINIFY", "true").lower() == "true",
            "base_url": hugo_config.get("baseURL"),
            "environment": get_env("HUGO_ENVIRONMENT", "production"),
            "hugo_config": hugo_config,
            "base_config": base_config.get("deployment", {}).get("build", {})
        }
    
    def _build_deploy_stage_config(self, base_config: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """Build configuration for Stage 5: Deployment."""
        return {
            "source_dir": get_env("DEPLOY_SOURCE_DIR", "hugo/public"),
            "target": get_env("DEPLOYMENT_TARGET", "github-pages"),
            "environment": environment,
            "auto_deploy": get_env("AUTO_DEPLOY", "true").lower() == "true",
            "prepare_only": get_env("PREPARE_ONLY", "false").lower() == "true",
            "base_config": base_config.get("deployment", {})
        }
    
    def _build_paths_config(self) -> Dict[str, str]:
        """Build standardized paths configuration."""
        return {
            "project_root": str(self.project_root),
            "notion_markdown": get_env("NOTION_OUTPUT_DIR", "notion_markdown"),
            "hugo_markdown": get_env("PROCESS_OUTPUT_DIR", "hugo_markdown"),
            "hugo_content": get_env("INTEGRATE_OUTPUT_DIR", "hugo/content"),
            "hugo_public": get_env("BUILD_OUTPUT_DIR", "hugo/public"),
            "hugo_root": self.config_manager.get_hugo_root_path(),
            "state_file": get_env("STATE_FILE", "src/config/.notion-hugo-state.json")
        }
    
    def validate_complete_pipeline(self) -> Dict[str, Any]:
        """
        Comprehensive validation of the entire 5-stage pipeline configuration.
        
        Returns:
            Validation results with detailed error information
        """
        if self._validation_results is None:
            self._validation_results = self._run_complete_validation()
        
        return self._validation_results
    
    def _run_complete_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all pipeline stages."""
        results = {
            "overall_valid": True,
            "errors": [],
            "warnings": [],
            "stage_results": {},
            "environment_status": {},
            "dependency_status": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            config = self.load_complete_config()
            
            # Validate each pipeline stage
            for stage_name in ["notion", "process", "integrate", "build", "deploy"]:
                stage_result = self._validate_pipeline_stage(stage_name, config)
                results["stage_results"][stage_name] = stage_result
                
                if not stage_result["valid"]:
                    results["overall_valid"] = False
                    results["errors"].extend(stage_result.get("errors", []))
                
                results["warnings"].extend(stage_result.get("warnings", []))
            
            # Validate environment variables
            results["environment_status"] = self._validate_environment_variables()
            
            # Validate dependencies
            results["dependency_status"] = self._validate_dependencies()
            
        except Exception as e:
            results["overall_valid"] = False
            results["errors"].append(f"Configuration validation failed: {str(e)}")
        
        return results
    
    def _validate_pipeline_stage(self, stage_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific pipeline stage configuration."""
        stage_config = config["pipeline"]["stages"].get(stage_name, {})
        result = {"valid": True, "errors": [], "warnings": []}
        
        if stage_name == "notion":
            # Validate Notion configuration
            if not stage_config.get("token"):
                result["errors"].append("NOTION_TOKEN is required for Notion sync")
                result["valid"] = False
            
            if not stage_config.get("database_id"):
                result["errors"].append("NOTION_DATABASE_ID is required for Notion sync")
                result["valid"] = False
            
            # Validate token format
            token = stage_config.get("token", "")
            if token and not token.startswith("ntn_"):
                result["warnings"].append("NOTION_TOKEN should start with 'ntn_'")
        
        elif stage_name == "process":
            # Validate processing configuration
            input_dir = Path(stage_config.get("input_dir", ""))
            if not input_dir.exists():
                result["warnings"].append(f"Process input directory does not exist: {input_dir}")
        
        elif stage_name == "integrate":
            # Validate integration configuration
            hugo_content_dir = stage_config.get("hugo_content_dir", "")
            if hugo_content_dir:
                content_path = Path(hugo_content_dir)
                if not content_path.parent.exists():
                    result["warnings"].append(f"Hugo content parent directory does not exist: {content_path.parent}")
        
        elif stage_name == "build":
            # Validate build configuration
            base_url = stage_config.get("base_url")
            if not base_url or base_url == "http://localhost:1313":
                result["warnings"].append("Base URL is set to localhost - update for production deployment")
        
        elif stage_name == "deploy":
            # Validate deployment configuration
            target = stage_config.get("target", "")
            if target == "github-pages" and not config.get("github", {}).get("owner"):
                result["errors"].append("GitHub repository information required for GitHub Pages deployment")
                result["valid"] = False
        
        return result
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variable configuration."""
        required_vars = ["NOTION_TOKEN"]
        recommended_vars = ["NOTION_DATABASE_ID", "SITE_TITLE", "SITE_AUTHOR"]
        
        all_valid, missing_required = self.env_mapper.validate_required_variables(required_vars)
        _, missing_recommended = self.env_mapper.validate_required_variables(recommended_vars)
        
        return {
            "required_valid": all_valid,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "migration_report": self.env_mapper.get_migration_report()
        }
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """Validate external dependencies."""
        dependencies = {
            "hugo_installed": self._check_hugo_installed(),
            "git_available": self._check_git_available(),
            "python_version": self._check_python_version()
        }
        
        return dependencies
    
    def _check_hugo_installed(self) -> Dict[str, Any]:
        """Check if Hugo is installed and get version."""
        try:
            import subprocess
            result = subprocess.run(["hugo", "version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {"available": True, "version": result.stdout.strip()}
            else:
                return {"available": False, "error": "Hugo command failed"}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"available": False, "error": "Hugo not found in PATH"}
    
    def _check_git_available(self) -> Dict[str, Any]:
        """Check if Git is available."""
        try:
            import subprocess
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {"available": True, "version": result.stdout.strip()}
            else:
                return {"available": False, "error": "Git command failed"}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"available": False, "error": "Git not found in PATH"}
    
    def _check_python_version(self) -> Dict[str, Any]:
        """Check Python version compatibility."""
        import sys
        version = sys.version_info
        
        if version >= (3, 8):
            return {
                "compatible": True,
                "version": f"{version.major}.{version.minor}.{version.micro}"
            }
        else:
            return {
                "compatible": False,
                "version": f"{version.major}.{version.minor}.{version.micro}",
                "error": "Python 3.8+ required"
            }
    
    # Convenience methods for accessing specific configurations
    def get_notion_config(self) -> Dict[str, Any]:
        """Get Notion pipeline stage configuration."""
        config = self.load_complete_config()
        return config["pipeline"]["stages"]["notion"]
    
    def get_hugo_config(self) -> Dict[str, Any]:
        """Get Hugo configuration."""
        config = self.load_complete_config()
        return config["hugo"]
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """Get deployment pipeline stage configuration."""
        config = self.load_complete_config()
        return config["pipeline"]["stages"]["deploy"]
    
    def get_paths_config(self) -> Dict[str, str]:
        """Get standardized paths configuration."""
        config = self.load_complete_config()
        return config["paths"]
    
    def is_ready_for_deployment(self) -> Tuple[bool, List[str]]:
        """
        Check if configuration is ready for deployment.
        
        Returns:
            Tuple of (is_ready, list_of_issues)
        """
        validation = self.validate_complete_pipeline()
        
        if validation["overall_valid"]:
            return True, []
        else:
            issues = validation["errors"] + [
                f"Warning: {w}" for w in validation["warnings"]
            ]
            return False, issues
    
    def create_configuration_report(self) -> str:
        """
        Create a comprehensive configuration report.
        
        Returns:
            Formatted string report of current configuration status
        """
        config = self.load_complete_config()
        validation = self.validate_complete_pipeline()
        
        report_lines = [
            "═══════════════════════════════════════════════════════════",
            "                NOTION-HUGO CONFIGURATION REPORT",
            "═══════════════════════════════════════════════════════════",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Environment: {config['pipeline']['environment']}",
            f"Deployment Target: {config['pipeline']['deployment_target']}",
            "",
            "PIPELINE VALIDATION STATUS:",
            f"Overall Status: {'✅ VALID' if validation['overall_valid'] else '❌ INVALID'}",
            ""
        ]
        
        # Stage validation results
        for stage_name, result in validation["stage_results"].items():
            status = "✅" if result["valid"] else "❌"
            report_lines.append(f"  Stage {stage_name.capitalize()}: {status}")
            
            for error in result.get("errors", []):
                report_lines.append(f"    ❌ {error}")
            
            for warning in result.get("warnings", []):
                report_lines.append(f"    ⚠️  {warning}")
        
        # Environment variables status
        env_status = validation["environment_status"]
        report_lines.extend([
            "",
            "ENVIRONMENT VARIABLES:",
            f"Required Variables: {'✅' if env_status['required_valid'] else '❌'}"
        ])
        
        for var in env_status.get("missing_required", []):
            report_lines.append(f"  ❌ Missing: {var}")
        
        for var in env_status.get("missing_recommended", []):
            report_lines.append(f"  ⚠️  Recommended: {var}")
        
        # Migration status
        migration = env_status["migration_report"]
        if migration["legacy_variables_found"]:
            report_lines.extend([
                "",
                "LEGACY VARIABLES (Please migrate):"
            ])
            for item in migration["legacy_variables_found"]:
                report_lines.append(f"  🔄 {item['legacy']} → {item['suggested']}")
        
        # Dependencies
        deps = validation["dependency_status"]
        report_lines.extend([
            "",
            "DEPENDENCIES:",
            f"Hugo: {'✅' if deps['hugo_installed']['available'] else '❌'}",
            f"Git: {'✅' if deps['git_available']['available'] else '❌'}",
            f"Python: {'✅' if deps['python_version']['compatible'] else '❌'}"
        ])
        
        report_lines.append("═══════════════════════════════════════════════════════════")
        
        return "\n".join(report_lines)


# Global instance for easy access
unified_config = UnifiedConfigLoader()

# Convenience functions
def load_pipeline_config() -> Dict[str, Any]:
    """Load complete pipeline configuration."""
    return unified_config.load_complete_config()

def validate_pipeline() -> Dict[str, Any]:
    """Validate complete pipeline configuration."""
    return unified_config.validate_complete_pipeline()

def is_deployment_ready() -> Tuple[bool, List[str]]:
    """Check if configuration is ready for deployment."""
    return unified_config.is_ready_for_deployment()

def get_configuration_report() -> str:
    """Get comprehensive configuration report."""
    return unified_config.create_configuration_report()