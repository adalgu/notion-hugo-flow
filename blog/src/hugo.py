#!/usr/bin/env python3
"""
Hugo Pipeline CLI

Command-line interface for the Hugo build pipeline.
Usage: python hugo.py build [options]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from hugo.pipeline import HugoPipeline
from hugo.config import HugoConfig


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point for Hugo pipeline"""
    parser = argparse.ArgumentParser(description="Hugo Static Site Build Pipeline")
    
    # Global options
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--config", type=Path, help="Configuration file path")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Hugo pipeline commands")
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build Hugo static site")
    build_parser.add_argument("--production", action="store_true", help="Build for production (default)")
    build_parser.add_argument("--development", action="store_true", help="Build for development")
    build_parser.add_argument("--theme", help="Hugo theme to use")
    build_parser.add_argument("--config-file", type=Path, help="Hugo config file")
    build_parser.add_argument("--output-dir", type=Path, help="Build output directory")
    build_parser.add_argument("--verbose", action="store_true", help="Verbose Hugo output")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start Hugo development server")
    serve_parser.add_argument("--port", type=int, default=1313, help="Server port")
    serve_parser.add_argument("--host", default="localhost", help="Server host")
    
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
        
        pipeline = HugoPipeline(config.get("hugo", {}))
        
        if args.command == "build":
            # Prepare build arguments
            build_kwargs = {}
            
            if args.theme:
                build_kwargs["theme"] = args.theme
            if args.config_file:
                build_kwargs["config_file"] = args.config_file
            if args.output_dir:
                build_kwargs["output_dir"] = args.output_dir
            if args.verbose:
                build_kwargs["verbose"] = True
                
            # Determine build mode
            if args.development:
                build_kwargs["build_mode"] = "development"
            else:
                build_kwargs["build_mode"] = "production"  # Default
            
            # Run build
            logger.info("Starting Hugo build...")
            result = pipeline.run(**build_kwargs)
            
            if result.success:
                build_info = result.data.get("build_info", {})
                file_counts = result.data.get("generated_files", {})
                
                logger.info(f"✅ Hugo build completed successfully!")
                logger.info(f"   Output: {result.data.get('output_directory', 'Unknown')}")
                logger.info(f"   Pages: {build_info.get('total_pages', 0)}")
                logger.info(f"   Files: {file_counts.get('total', 0)}")
                logger.info(f"   Duration: {result.duration:.1f}s")
                
                if build_info.get('build_duration'):
                    logger.info(f"   Hugo time: {build_info['build_duration']}")
            else:
                logger.error(f"❌ Hugo build failed:")
                for error in result.errors:
                    logger.error(f"   {error}")
                
                # Show build log if available
                build_log = result.data.get("build_log", {})
                if build_log.get("stderr"):
                    logger.error("Build errors:")
                    logger.error(build_log["stderr"])
                
                sys.exit(1)
        
        elif args.command == "serve":
            logger.info("Hugo serve functionality not yet implemented")
            logger.info("Please use 'hugo serve' command directly for now")
            
            # Show equivalent Hugo command
            hugo_config = pipeline.hugo_config
            cmd_args = hugo_config.hugo_serve_args
            logger.info(f"Equivalent command: hugo {' '.join(cmd_args)}")
        
        elif args.command == "status":
            status = pipeline.get_status()
            state = status["state"]
            
            print(f"\n=== Hugo Pipeline Status ===")
            print(f"Current Status: {state['status']}")
            print(f"Last Run: {state['last_run'] or 'Never'}")
            print(f"Last Success: {state['last_success'] or 'Never'}")
            print(f"Total Runs: {state['run_count']}")
            print(f"Error Count: {state['error_count']}")
            
            if state['last_error']:
                print(f"Last Error: {state['last_error']}")
            
            # Show configuration
            config_valid = pipeline.hugo_config.is_valid
            print(f"Configuration Valid: {'✅' if config_valid else '❌'}")
            
            if not config_valid:
                errors = pipeline.hugo_config.validate()
                print("Configuration Issues:")
                for error in errors:
                    print(f"  - {error}")
            
            # Show Hugo availability
            import subprocess
            try:
                result = subprocess.run(["hugo", "version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Hugo Available: ✅")
                    # Extract version from output
                    version_line = result.stdout.split('\n')[0]
                    print(f"Hugo Version: {version_line}")
                else:
                    print(f"Hugo Available: ❌")
            except FileNotFoundError:
                print(f"Hugo Available: ❌ (not found in PATH)")
            
            # Show theme status
            theme_path = pipeline.hugo_config.get_theme_path()
            if theme_path:
                print(f"Theme Available: ✅ ({theme_path})")
            else:
                print(f"Theme Available: ❌ ({pipeline.hugo_config.theme})")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()