#!/usr/bin/env python3
"""
Environment Variable Mapper for Notion-Hugo CLI

This module provides backward-compatible environment variable mapping
from complex legacy names to simplified new names as defined in MIGRATION_PLAN.md.

Key mappings:
- NOTION_DATABASE_ID_POSTS -> NOTION_DATABASE_ID
- HUGO_SITE_BASE_URL -> HUGO_BASE_URL
- SITE_TITLE -> HUGO_SITE_TITLE (when used with Hugo)

Supports deprecation warnings and gradual migration.
"""

import os
import warnings
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime


class EnvironmentVariableMapper:
    """
    Maps legacy environment variables to simplified names with deprecation warnings.
    
    Provides backward compatibility during the migration from complex to simple
    environment variable names.
    """
    
    # Mapping from legacy names to new simplified names
    LEGACY_MAPPINGS: Dict[str, str] = {
        # Notion configuration
        "NOTION_DATABASE_ID_POSTS": "NOTION_DATABASE_ID",
        "NOTION_DATABASE_ID_PAGES": "NOTION_PAGE_ID",
        
        # Hugo/Site configuration  
        "HUGO_SITE_BASE_URL": "HUGO_BASE_URL",
        "HUGO_SITE_TITLE": "SITE_TITLE",
        "HUGO_SITE_DESCRIPTION": "SITE_DESCRIPTION", 
        "HUGO_SITE_AUTHOR": "SITE_AUTHOR",
        
        # Deployment configuration
        "DEPLOYMENT_ENVIRONMENT": "DEPLOY_ENVIRONMENT",
        "GITHUB_ACTIONS_AUTO_DEPLOY": "AUTO_DEPLOY",
        
        # Security configuration
        "SECURITY_LOGGING_MASK_SENSITIVE_DATA": "MASK_SENSITIVE_DATA",
        "SECURITY_ENVIRONMENT_VARIABLES_VALIDATE_ENV_VARS": "VALIDATE_ENV_VARS",
    }
    
    # Reverse mapping for looking up new names
    NEW_TO_LEGACY: Dict[str, str] = {v: k for k, v in LEGACY_MAPPINGS.items()}
    
    def __init__(self, enable_warnings: bool = True):
        """
        Initialize the environment variable mapper.
        
        Args:
            enable_warnings: Whether to show deprecation warnings for legacy variables
        """
        self.enable_warnings = enable_warnings
        self._warned_variables: set = set()
    
    def get_env_value(self, new_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value using new simplified name, with legacy fallback.
        
        Args:
            new_name: The new simplified environment variable name
            default: Default value if neither new nor legacy variable is found
            
        Returns:
            The environment variable value, or default if not found
        """
        # First try the new simplified name
        value = os.environ.get(new_name)
        if value is not None:
            return value
        
        # If not found, try the legacy name
        legacy_name = self.NEW_TO_LEGACY.get(new_name)
        if legacy_name:
            legacy_value = os.environ.get(legacy_name)
            if legacy_value is not None:
                # Show deprecation warning (only once per variable)
                if self.enable_warnings and legacy_name not in self._warned_variables:
                    self._warn_legacy_variable(legacy_name, new_name)
                    self._warned_variables.add(legacy_name)
                return legacy_value
        
        return default
    
    def _warn_legacy_variable(self, legacy_name: str, new_name: str) -> None:
        """
        Show deprecation warning for legacy environment variable.
        
        Args:
            legacy_name: The legacy environment variable name
            new_name: The new simplified name to use instead
        """
        warnings.warn(
            f"Environment variable '{legacy_name}' is deprecated. "
            f"Please use '{new_name}' instead. "
            f"Legacy support will be removed in a future version.",
            DeprecationWarning,
            stacklevel=3
        )
    
    def get_all_mapped_values(self) -> Dict[str, Optional[str]]:
        """
        Get all environment variables using the new simplified names.
        
        Returns:
            Dictionary mapping new variable names to their values
        """
        result = {}
        
        # Get all possible new variable names
        all_new_names = set(self.NEW_TO_LEGACY.keys())
        
        # Also check for direct new names that might not have legacy equivalents
        for key, value in os.environ.items():
            # Check common patterns for simplified names
            if any(key.startswith(prefix) for prefix in [
                "NOTION_", "HUGO_", "SITE_", "DEPLOY_", "AUTO_"
            ]):
                all_new_names.add(key)
        
        for new_name in all_new_names:
            result[new_name] = self.get_env_value(new_name)
        
        return {k: v for k, v in result.items() if v is not None}
    
    def validate_required_variables(self, required: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that all required environment variables are set.
        
        Args:
            required: List of required environment variable names (using new names)
            
        Returns:
            Tuple of (all_found, missing_variables)
        """
        missing = []
        
        for var_name in required:
            if self.get_env_value(var_name) is None:
                missing.append(var_name)
        
        return len(missing) == 0, missing
    
    def get_migration_report(self) -> Dict[str, Any]:
        """
        Generate a report showing current environment variable usage.
        
        Returns:
            Dictionary containing migration status information
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "legacy_variables_found": [],
            "new_variables_found": [],
            "missing_recommended": [],
            "migration_progress": 0.0
        }
        
        # Check what variables are currently set
        for legacy_name, new_name in self.LEGACY_MAPPINGS.items():
            legacy_value = os.environ.get(legacy_name)
            new_value = os.environ.get(new_name)
            
            if legacy_value and not new_value:
                report["legacy_variables_found"].append({
                    "legacy": legacy_name,
                    "suggested": new_name,
                    "value_preview": f"{legacy_value[:10]}..." if len(legacy_value) > 10 else legacy_value
                })
            elif new_value:
                report["new_variables_found"].append({
                    "name": new_name,
                    "value_preview": f"{new_value[:10]}..." if len(new_value) > 10 else new_value
                })
        
        # Calculate migration progress
        total_mappings = len(self.LEGACY_MAPPINGS)
        migrated_count = len(report["new_variables_found"])
        if total_mappings > 0:
            report["migration_progress"] = migrated_count / total_mappings
        
        # Recommended variables that should be set
        recommended_vars = [
            "NOTION_TOKEN", "NOTION_DATABASE_ID", "HUGO_BASE_URL", 
            "SITE_TITLE", "SITE_AUTHOR"
        ]
        
        for var in recommended_vars:
            if not self.get_env_value(var):
                report["missing_recommended"].append(var)
        
        return report
    
    def create_env_template(self, file_path: str = ".env.example") -> bool:
        """
        Create a .env template file with the new simplified variable names.
        
        Args:
            file_path: Path where to create the template file
            
        Returns:
            True if template was created successfully
        """
        template_content = f"""# Notion-Hugo Environment Variables Configuration
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Copy this file to .env and fill in your actual values

# 🔴 Required: Notion API Configuration
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here

# 🟡 Optional: Additional Notion Configuration  
NOTION_PAGE_ID=your_page_id_for_single_pages

# 🟢 Optional: Hugo Site Configuration
HUGO_BASE_URL=https://yourdomain.com
SITE_TITLE=Your Blog Title
SITE_DESCRIPTION=Your blog description
SITE_AUTHOR=Your Name

# 🟢 Optional: Deployment Configuration
DEPLOY_ENVIRONMENT=production
AUTO_DEPLOY=true

# 🟢 Optional: Security Settings
MASK_SENSITIVE_DATA=true
VALIDATE_ENV_VARS=true

# 🟢 Optional: Hugo Build Settings
HUGO_VERSION=0.140.0
HUGO_EXTENDED=true

# Legacy variables (deprecated - migrate to above):
# NOTION_DATABASE_ID_POSTS -> NOTION_DATABASE_ID
# HUGO_SITE_BASE_URL -> HUGO_BASE_URL  
# HUGO_SITE_TITLE -> SITE_TITLE
# HUGO_SITE_DESCRIPTION -> SITE_DESCRIPTION
# HUGO_SITE_AUTHOR -> SITE_AUTHOR
"""
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            return True
        except Exception:
            return False


# Global instance for easy access
env_mapper = EnvironmentVariableMapper()

# Convenience functions
def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with legacy fallback support."""
    return env_mapper.get_env_value(name, default)

def validate_required_env(required_vars: List[str]) -> Tuple[bool, List[str]]:
    """Validate required environment variables are set."""
    return env_mapper.validate_required_variables(required_vars)

def create_env_template(path: str = ".env.example") -> bool:
    """Create environment variable template file."""
    return env_mapper.create_env_template(path)