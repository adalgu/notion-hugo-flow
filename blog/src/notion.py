#!/usr/bin/env python3
"""
Notion Pipeline CLI

Command-line interface for the Notion sync pipeline.
Usage: python notion.py sync [options]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from notion.pipeline import NotionPipeline
from notion.config import NotionConfig


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point for Notion pipeline"""
    parser = argparse.ArgumentParser(description="Notion Content Sync Pipeline")
    
    # Global options
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--config", type=Path, help="Configuration file path")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Notion pipeline commands")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync content from Notion")
    sync_parser.add_argument("--full", action="store_true", help="Perform full sync instead of incremental")
    sync_parser.add_argument("--dry-run", action="store_true", help="Simulate sync without making changes")
    sync_parser.add_argument("--token", help="Notion API token")
    sync_parser.add_argument("--database-id", help="Notion database ID")
    sync_parser.add_argument("--output-dir", type=Path, help="Output directory for markdown files")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show pipeline status")
    
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
        
        pipeline = NotionPipeline(config.get("notion", {}))
        
        if args.command == "sync":
            # Prepare sync arguments
            sync_kwargs = {}
            
            if args.token:
                sync_kwargs["token"] = args.token
            if args.database_id:
                sync_kwargs["database_id"] = args.database_id
            if args.output_dir:
                sync_kwargs["output_dir"] = str(args.output_dir)
            if args.full:
                sync_kwargs["sync_mode"] = "full"
            if args.dry_run:
                sync_kwargs["dry_run"] = True
            
            # Run sync
            logger.info("Starting Notion sync...")
            result = pipeline.run(**sync_kwargs)
            
            if result.success:
                sync_state = result.data.get("sync_state", {})
                logger.info(f"✅ Notion sync completed successfully!")
                logger.info(f"   Processed: {sync_state.get('processed_count', 0)} items")
                logger.info(f"   New files: {sync_state.get('new_files', 0)}")
                logger.info(f"   Updated: {sync_state.get('updated_files', 0)}")
                logger.info(f"   Duration: {result.duration:.1f}s")
                
                if args.dry_run:
                    logger.info("   (Dry run - no files were actually created)")
            else:
                logger.error(f"❌ Notion sync failed:")
                for error in result.errors:
                    logger.error(f"   {error}")
                sys.exit(1)
        
        elif args.command == "status":
            status = pipeline.get_status()
            state = status["state"]
            
            print(f"\n=== Notion Pipeline Status ===")
            print(f"Current Status: {state['status']}")
            print(f"Last Run: {state['last_run'] or 'Never'}")
            print(f"Last Success: {state['last_success'] or 'Never'}")
            print(f"Total Runs: {state['run_count']}")
            print(f"Error Count: {state['error_count']}")
            
            if state['last_error']:
                print(f"Last Error: {state['last_error']}")
            
            # Show configuration
            config_valid = pipeline.notion_config.is_valid
            print(f"Configuration Valid: {'✅' if config_valid else '❌'}")
            
            if not config_valid:
                errors = pipeline.notion_config.validate()
                print("Configuration Issues:")
                for error in errors:
                    print(f"  - {error}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()