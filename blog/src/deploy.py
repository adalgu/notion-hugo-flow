#!/usr/bin/env python3
"""
Deployment Pipeline CLI

Command-line interface for the deployment pipeline.
Usage: python deploy.py github [options]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from deployment.pipeline import DeploymentPipeline
from deployment.config import DeploymentConfig


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point for deployment pipeline"""
    parser = argparse.ArgumentParser(description="Site Deployment Pipeline")
    
    # Global options
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--site-dir", type=Path, help="Site directory to deploy")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deployment without actually deploying")
    
    # Subcommands for different platforms
    subparsers = parser.add_subparsers(dest="platform", help="Deployment platform")
    
    # GitHub Pages
    github_parser = subparsers.add_parser("github", help="Deploy to GitHub Pages")
    github_parser.add_argument("--token", help="GitHub personal access token")
    github_parser.add_argument("--repository", help="GitHub repository (user/repo format)")
    github_parser.add_argument("--branch", default="gh-pages", help="Target branch")
    
    # Vercel
    vercel_parser = subparsers.add_parser("vercel", help="Deploy to Vercel")
    vercel_parser.add_argument("--token", help="Vercel API token")
    vercel_parser.add_argument("--project-id", help="Vercel project ID")
    
    # Netlify
    netlify_parser = subparsers.add_parser("netlify", help="Deploy to Netlify")
    netlify_parser.add_argument("--token", help="Netlify API token")
    netlify_parser.add_argument("--site-id", help="Netlify site ID")
    
    # Status and history commands
    status_parser = subparsers.add_parser("status", help="Show deployment status")
    history_parser = subparsers.add_parser("history", help="Show deployment history")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize pipeline
        config = {}
        if args.config and args.config.exists():
            import yaml
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        
        pipeline = DeploymentPipeline(config.get("deployment", {}))
        
        if args.platform in ["github", "vercel", "netlify"]:
            # Prepare deployment arguments
            deploy_kwargs = {}
            
            # Map platform name
            platform_map = {
                "github": "github_pages",
                "vercel": "vercel",
                "netlify": "netlify"
            }
            deploy_kwargs["platform"] = platform_map[args.platform]
            
            if args.site_dir:
                deploy_kwargs["site_directory"] = str(args.site_dir)
            if args.dry_run:
                deploy_kwargs["dry_run"] = True
            
            # Platform-specific arguments
            if args.platform == "github":
                if args.token:
                    deploy_kwargs["github_token"] = args.token
                if args.repository:
                    deploy_kwargs["github_repository"] = args.repository
                if args.branch:
                    deploy_kwargs["github_branch"] = args.branch
            
            elif args.platform == "vercel":
                if args.token:
                    deploy_kwargs["vercel_token"] = args.token
                if args.project_id:
                    deploy_kwargs["vercel_project_id"] = args.project_id
            
            elif args.platform == "netlify":
                if args.token:
                    deploy_kwargs["netlify_token"] = args.token
                if args.site_id:
                    deploy_kwargs["netlify_site_id"] = args.site_id
            
            # Run deployment
            logger.info(f"Starting deployment to {args.platform}...")
            result = pipeline.run(**deploy_kwargs)
            
            if result.success:
                deployment_url = result.data.get("deployment_url", "Unknown")
                file_stats = result.data.get("file_stats", {})
                details = result.data.get("deployment_details", {})
                
                if args.dry_run:
                    logger.info(f"✅ Dry run completed successfully!")
                    logger.info(f"   Would deploy to: {deployment_url}")
                    logger.info(f"   Files to upload: {file_stats.get('total_files', 0)}")
                    logger.info(f"   Total size: {details.get('total_size', 'Unknown')}")
                else:
                    logger.info(f"✅ Deployment completed successfully!")
                    logger.info(f"   Site URL: {deployment_url}")
                    logger.info(f"   Files uploaded: {details.get('files_uploaded', file_stats.get('total_files', 0))}")
                    logger.info(f"   Total size: {details.get('total_size', 'Unknown')}")
                    logger.info(f"   Duration: {result.duration:.1f}s")
            else:
                logger.error(f"❌ Deployment failed:")
                for error in result.errors:
                    logger.error(f"   {error}")
                sys.exit(1)
        
        elif args.platform == "status":
            status = pipeline.get_status()
            state = status["state"]
            
            print(f"\n=== Deployment Pipeline Status ===")
            print(f"Current Status: {state['status']}")
            print(f"Last Run: {state['last_run'] or 'Never'}")
            print(f"Last Success: {state['last_success'] or 'Never'}")
            print(f"Total Runs: {state['run_count']}")
            print(f"Error Count: {state['error_count']}")
            
            if state['last_error']:
                print(f"Last Error: {state['last_error']}")
            
            # Show configuration
            config_valid = pipeline.deployment_config.is_valid
            print(f"Configuration Valid: {'✅' if config_valid else '❌'}")
            
            if not config_valid:
                errors = pipeline.deployment_config.validate()
                print("Configuration Issues:")
                for error in errors:
                    print(f"  - {error}")
            
            # Show platform configuration
            platform_config = pipeline.deployment_config.platform_config
            print(f"\nConfigured Platform: {pipeline.deployment_config.platform}")
            print(f"Expected URL: {pipeline.deployment_config.get_deployment_url() or 'Not configured'}")
        
        elif args.platform == "history":
            logger.info("Deployment history functionality not yet implemented")
            logger.info("Check .pipeline-state.json for basic status information")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()