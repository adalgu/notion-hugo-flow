"""
Hugo Pipeline Configuration

Manages configuration for Hugo static site generation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HugoConfig:
    """Configuration for Hugo pipeline"""
    
    # Directory configuration
    content_dir: str = "blog/content"
    static_dir: str = "blog/static"
    layouts_dir: str = "blog/layouts"
    output_dir: str = "blog/public"
    
    # Hugo configuration
    config_file: str = "blog/config.yaml"
    theme: str = "PaperMod"
    base_url: str = "http://localhost:1313"
    
    # Build configuration
    build_mode: str = "production"  # "production" or "development"
    minify: bool = True
    enable_git_info: bool = True
    build_drafts: bool = False
    build_future: bool = False
    
    # Performance configuration
    build_timeout: int = 60  # seconds
    max_parallel: int = 4
    
    # Server configuration (for development)
    server_port: int = 1313
    server_host: str = "localhost"
    server_watch: bool = True
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        if config_dict:
            # Map config dictionary to attributes
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Ensure paths are Path objects
        self.content_dir = Path(self.content_dir)
        self.static_dir = Path(self.static_dir)
        self.layouts_dir = Path(self.layouts_dir)
        self.output_dir = Path(self.output_dir)
        self.config_file = Path(self.config_file)
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(
            self.config_file.exists() and 
            self.content_dir.exists()
        )
    
    @property
    def hugo_args(self) -> List[str]:
        """Get Hugo command arguments based on configuration"""
        args = []
        
        # Basic configuration
        args.extend(["--config", str(self.config_file)])
        args.extend(["--theme", self.theme])
        args.extend(["--destination", str(self.output_dir)])
        
        # Build mode specific args
        if self.build_mode == "production":
            if self.minify:
                args.append("--minify")
            args.append("--gc")  # Garbage collection
        
        elif self.build_mode == "development":
            if self.build_drafts:
                args.append("--buildDrafts")
            if self.build_future:
                args.append("--buildFuture")
        
        # Additional options
        if self.enable_git_info:
            args.append("--enableGitInfo")
        
        return args
    
    @property
    def hugo_serve_args(self) -> List[str]:
        """Get Hugo serve command arguments"""
        args = self.hugo_args.copy()
        
        # Replace build-specific args for serve
        if "--destination" in args:
            dest_idx = args.index("--destination")
            # Remove --destination and its value
            args.pop(dest_idx + 1)  # Remove path
            args.pop(dest_idx)      # Remove --destination
        
        if "--minify" in args:
            args.remove("--minify")
        
        if "--gc" in args:
            args.remove("--gc")
        
        # Add serve-specific options
        args.extend(["--port", str(self.server_port)])
        args.extend(["--bind", self.server_host])
        
        if self.server_watch:
            args.append("--watch")
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "content_dir": str(self.content_dir),
            "static_dir": str(self.static_dir),
            "layouts_dir": str(self.layouts_dir),
            "output_dir": str(self.output_dir),
            "config_file": str(self.config_file),
            "theme": self.theme,
            "base_url": self.base_url,
            "build_mode": self.build_mode,
            "minify": self.minify,
            "enable_git_info": self.enable_git_info,
            "build_drafts": self.build_drafts,
            "build_future": self.build_future,
            "build_timeout": self.build_timeout,
            "max_parallel": self.max_parallel,
            "server_port": self.server_port,
            "server_host": self.server_host,
            "server_watch": self.server_watch
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.config_file.exists():
            errors.append(f"Hugo config file does not exist: {self.config_file}")
        
        if not self.content_dir.exists():
            errors.append(f"Content directory does not exist: {self.content_dir}")
        
        if self.build_mode not in ["production", "development"]:
            errors.append("build_mode must be 'production' or 'development'")
        
        if self.build_timeout < 1:
            errors.append("build_timeout must be greater than 0")
        
        if not (1 <= self.server_port <= 65535):
            errors.append("server_port must be between 1 and 65535")
        
        return errors
    
    def get_theme_path(self) -> Optional[Path]:
        """Get the path to the theme directory"""
        # Check for theme as git submodule
        theme_paths = [
            Path("blog/themes") / self.theme,
            Path("themes") / self.theme,
            Path("blog") / self.theme  # For submodule in blog directory
        ]
        
        for theme_path in theme_paths:
            if theme_path.exists() and theme_path.is_dir():
                return theme_path
        
        return None
    
    def ensure_theme_available(self) -> bool:
        """Check if theme is available and accessible"""
        theme_path = self.get_theme_path()
        return theme_path is not None and (theme_path / "theme.toml").exists()