"""
Deployment Pipeline Module

This module handles the deployment of Hugo-built static sites to various platforms.
It provides a clean interface for deploying to GitHub Pages, Vercel, Netlify, and other platforms.

Core Components:
- pipeline.py: Main pipeline orchestration
- github.py: GitHub Pages deployment logic  
- vercel.py: Vercel deployment logic
- config.py: Deployment-specific configuration management
"""

from .pipeline import DeploymentPipeline
from .config import DeploymentConfig

__version__ = "1.0.0"
__all__ = ["DeploymentPipeline", "DeploymentConfig"]