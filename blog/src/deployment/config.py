"""
Deployment Pipeline Configuration

Manages configuration for static site deployment to various platforms.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DeploymentConfig:
    """Configuration for deployment pipeline"""
    
    # Site configuration
    site_directory: str = "blog/public"
    
    # Platform configuration
    platform: str = "github_pages"  # "github_pages", "vercel", "netlify"
    
    # GitHub Pages configuration
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    github_branch: str = "gh-pages"
    custom_domain: Optional[str] = None
    
    # Vercel configuration
    vercel_token: Optional[str] = None
    vercel_project_id: Optional[str] = None
    vercel_team_id: Optional[str] = None
    
    # Netlify configuration
    netlify_token: Optional[str] = None
    netlify_site_id: Optional[str] = None
    
    # Deployment options
    auto_deploy: bool = True
    cache_invalidation: bool = True
    compression: bool = True
    cdn_enabled: bool = True
    
    # Performance configuration
    deploy_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    # File handling
    ignore_patterns: List[str] = field(default_factory=lambda: [
        ".DS_Store",
        "*.log",
        "Thumbs.db",
        ".git*"
    ])
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        if config_dict:
            # Map config dictionary to attributes
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Ensure site_directory is a Path object
        if isinstance(self.site_directory, str):
            self.site_directory = Path(self.site_directory)
    
    @property
    def supported_platforms(self) -> List[str]:
        """Get list of supported deployment platforms"""
        return ["github_pages", "vercel", "netlify"]
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid for the selected platform"""
        if self.platform == "github_pages":
            return bool(self.github_token and self.github_repository)
        elif self.platform == "vercel":
            return bool(self.vercel_token and self.vercel_project_id)
        elif self.platform == "netlify":
            return bool(self.netlify_token and self.netlify_site_id)
        return False
    
    @property
    def platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        if self.platform == "github_pages":
            return {
                "token": self.github_token,
                "repository": self.github_repository,
                "branch": self.github_branch,
                "custom_domain": self.custom_domain
            }
        elif self.platform == "vercel":
            return {
                "token": self.vercel_token,
                "project_id": self.vercel_project_id,
                "team_id": self.vercel_team_id
            }
        elif self.platform == "netlify":
            return {
                "token": self.netlify_token,
                "site_id": self.netlify_site_id
            }
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "site_directory": str(self.site_directory),
            "platform": self.platform,
            "github_token": self.github_token,
            "github_repository": self.github_repository,
            "github_branch": self.github_branch,
            "custom_domain": self.custom_domain,
            "vercel_token": self.vercel_token,
            "vercel_project_id": self.vercel_project_id,
            "vercel_team_id": self.vercel_team_id,
            "netlify_token": self.netlify_token,
            "netlify_site_id": self.netlify_site_id,
            "auto_deploy": self.auto_deploy,
            "cache_invalidation": self.cache_invalidation,
            "compression": self.compression,
            "cdn_enabled": self.cdn_enabled,
            "deploy_timeout": self.deploy_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "ignore_patterns": self.ignore_patterns
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if self.platform not in self.supported_platforms:
            errors.append(f"Unsupported platform: {self.platform}")
        
        if not Path(self.site_directory).exists():
            errors.append(f"Site directory does not exist: {self.site_directory}")
        
        # Platform-specific validation
        if self.platform == "github_pages":
            if not self.github_token:
                errors.append("GitHub token is required for GitHub Pages deployment")
            if not self.github_repository:
                errors.append("GitHub repository is required for GitHub Pages deployment")
        
        elif self.platform == "vercel":
            if not self.vercel_token:
                errors.append("Vercel token is required for Vercel deployment")
            if not self.vercel_project_id:
                errors.append("Vercel project ID is required for Vercel deployment")
        
        elif self.platform == "netlify":
            if not self.netlify_token:
                errors.append("Netlify token is required for Netlify deployment")
            if not self.netlify_site_id:
                errors.append("Netlify site ID is required for Netlify deployment")
        
        # General validation
        if self.deploy_timeout < 1:
            errors.append("deploy_timeout must be greater than 0")
        
        if self.max_retries < 0:
            errors.append("max_retries cannot be negative")
        
        if self.retry_delay < 0:
            errors.append("retry_delay cannot be negative")
        
        return errors
    
    def get_deployment_url(self) -> Optional[str]:
        """Get the expected deployment URL"""
        if self.platform == "github_pages":
            if self.custom_domain:
                return f"https://{self.custom_domain}"
            elif self.github_repository:
                # Parse username/repo format
                parts = self.github_repository.split("/")
                if len(parts) == 2:
                    username, repo = parts
                    return f"https://{username}.github.io/{repo}"
        
        elif self.platform == "vercel":
            if self.vercel_project_id:
                return f"https://{self.vercel_project_id}.vercel.app"
        
        elif self.platform == "netlify":
            if self.netlify_site_id:
                return f"https://{self.netlify_site_id}.netlify.app"
        
        return None
    
    def get_ignore_patterns(self) -> List[str]:
        """Get file patterns to ignore during deployment"""
        return self.ignore_patterns.copy()
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored during deployment"""
        import fnmatch
        
        file_name = file_path.name
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        
        return False