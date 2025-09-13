#!/usr/bin/env python3
"""
5-Stage Notion-Hugo Pipeline CLI

This CLI implements the refined 5-stage pipeline flow:
1. notion: Notion Database → notion_markdown/
2. process: notion_markdown/ → hugo_markdown/
3. integrate: hugo_markdown/ → hugo/content/
4. build: hugo/ → hugo/public/
5. deploy: hugo/public/ → hosting

Usage:
    python -m src notion      # Stage 1: Notion sync
    python -m src process     # Stage 2: Hugo processing
    python -m src integrate   # Stage 3: Content integration
    python -m src build       # Stage 4: Site build
    python -m src deploy      # Stage 5: Deployment
    python -m src run --full  # All stages
"""

import os
import sys
import click
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime

# Import CLI utilities
try:
    from .cli_utils import print_success, print_error, print_info, print_warning
except ImportError:
    # Fallback print functions
    def print_success(msg): print(f"✅ {msg}")
    def print_error(msg): print(f"❌ {msg}")
    def print_info(msg): print(f"ℹ️  {msg}")
    def print_warning(msg): print(f"⚠️  {msg}")

# Import pipeline components with configuration system
try:
    from .config import (
        UnifiedConfigLoader, 
        load_pipeline_config,
        validate_pipeline,
        is_deployment_ready,
        get_configuration_report,
        PipelineValidationError
    )
except ImportError as e:
    print_warning(f"Configuration system not available: {e}")
    UnifiedConfigLoader = None
    PipelineValidationError = Exception

# Mock implementation for components not yet fully implemented
class MockComponent:
    """Mock implementation for pipeline components not yet fully implemented."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def run(self, *args, **kwargs):
        return {"success": True, "message": "Mock implementation - component not yet implemented"}

# Import real pipeline components
try:
    from .notion import NotionPipeline
except ImportError:
    NotionPipeline = MockComponent

try:
    from .hugo.content_processor import ContentProcessor
except ImportError:
    ContentProcessor = MockComponent

try:
    from .hugo.integration import HugoIntegration
except ImportError:
    HugoIntegration = MockComponent

try:
    from .hugo.hugo_setup import BuildManager
except ImportError:
    BuildManager = MockComponent

try:
    from .deploy.deployment_manager import DeploymentManager
except ImportError:
    DeploymentManager = MockComponent


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if it doesn't."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print_error(f"Failed to create directory {path}: {e}")
        return False


def configure_portfolio_mode():
    """Configure environment for portfolio mode (gunn.kim)."""
    os.environ["HUGO_BASE_URL"] = "https://gunn.kim"
    os.environ["SITE_TITLE"] = "Gunn Kim - Tech Portfolio & Blog" 
    os.environ["SITE_AUTHOR"] = "Gunn Kim"
    os.environ["PORTFOLIO_MODE"] = "true"
    os.environ["DEPLOY_TARGET"] = "github_pages"
    os.environ["CUSTOM_DOMAIN"] = "gunn.kim"
    print_info("🎯 Portfolio mode configured for gunn.kim")


def validate_environment() -> bool:
    """Validate environment variables and configuration."""
    if UnifiedConfigLoader is None:
        # Fallback validation for when config system is not available
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            print_error("NOTION_TOKEN environment variable not set")
            print_info("Please set your Notion API token or run setup first")
            return False
        return True
    
    try:
        config_loader = UnifiedConfigLoader(enable_deprecation_warnings=True)
        is_ready, issues = config_loader.is_ready_for_deployment()
        
        if not is_ready:
            print_error("Configuration validation failed:")
            for issue in issues[:5]:  # Show first 5 issues
                print_error(f"  - {issue}")
            if len(issues) > 5:
                print_error(f"  ... and {len(issues) - 5} more issues")
            print_info("\nRun 'python -m src config-report' for detailed configuration status")
            return False
        
        # Show any deprecation warnings for legacy environment variables
        validation = config_loader.validate_complete_pipeline()
        env_status = validation.get("environment_status", {})
        migration = env_status.get("migration_report", {})
        
        if migration.get("legacy_variables_found"):
            print_warning("Legacy environment variables detected:")
            for item in migration["legacy_variables_found"][:3]:  # Show first 3
                print_warning(f"  {item['legacy']} → {item['suggested']}")
            if len(migration["legacy_variables_found"]) > 3:
                print_warning(f"  ... and {len(migration['legacy_variables_found']) - 3} more")
            print_info("Consider migrating to simplified variable names")
        
        return True
        
    except Exception as e:
        print_error(f"Environment validation failed: {e}")
        print_info("Falling back to basic validation")
        notion_token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_DATABASE_ID_POSTS")
        if not notion_token:
            print_error("NOTION_TOKEN environment variable not set")
            return False
        return True


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@click.pass_context
def cli(ctx, verbose: bool, dry_run: bool):
    """
    5-Stage Notion-Hugo Pipeline CLI
    
    Orchestrates the complete pipeline from Notion to deployed static site.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run
    
    if verbose:
        print_info("🚀 5-Stage Notion-Hugo Pipeline CLI initialized")
        if dry_run:
            print_info("🧪 Dry run mode: No actual changes will be made")


@cli.command()
@click.option("--incremental/--full-sync", default=True, help="Incremental or full sync")
@click.option("--output-dir", default=None, help="Output directory for markdown files")
@click.option("--state-file", default=None, help="State file for incremental sync")
@click.option("--portfolio", is_flag=True, help="Configure for portfolio mode (gunn.kim)")
@click.pass_context
def notion(ctx, incremental: bool, output_dir: Optional[str], state_file: Optional[str], portfolio: bool):
    """
    Stage 1: Notion Database → notion_markdown/
    
    Fetch content from Notion database and convert to clean markdown.
    """
    print_info("🎯 Stage 1: Notion Database → notion_markdown/")
    
    # Configure portfolio mode if requested
    if portfolio:
        configure_portfolio_mode()
    
    if ctx.obj.get('dry_run'):
        print_info("🧪 Dry run: Would sync Notion content to notion_markdown/")
        return
    
    try:
        # Load configuration if available
        if UnifiedConfigLoader is not None:
            config_loader = UnifiedConfigLoader()
            config = config_loader.load_complete_config()
            notion_config = config_loader.get_notion_config()
            
            # Use config values or fall back to CLI options
            actual_output_dir = output_dir or notion_config.get("output_dir", "notion_markdown")
            actual_state_file = state_file or notion_config.get("state_file", "src/config/.notion-hugo-state.json")
        else:
            # Fallback when config system not available
            actual_output_dir = output_dir or "notion_markdown"
            actual_state_file = state_file or "src/config/.notion-hugo-state.json"
            notion_config = {}
        
        # Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Ensure output directories exist
        for subdir in ['posts', 'pages']:
            if not ensure_directory(f"{actual_output_dir}/{subdir}"):
                sys.exit(1)
        
        # Initialize Notion pipeline with configuration
        if notion_config:
            pipeline = NotionPipeline(
                output_dir=actual_output_dir,
                state_file=actual_state_file,
                incremental=incremental,
                config=notion_config
            )
        else:
            pipeline = NotionPipeline(
                output_dir=actual_output_dir,
                state_file=actual_state_file,
                incremental=incremental
            )
        
        # Run the pipeline
        result = pipeline.run()
        
        if result.get("success"):
            file_count = result.get("file_count", 0)
            mode = "incremental" if incremental else "full sync"
            print_success(f"Stage 1 complete: {file_count} files processed ({mode})")
            print_info(f"📁 Output: {actual_output_dir}/")
        else:
            print_error(f"Stage 1 failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except PipelineValidationError as e:
        print_error(f"Configuration error: {e}")
        print_info("Run 'python -m src config-report' for detailed diagnostics")
        sys.exit(1)
    except Exception as e:
        print_error(f"Stage 1 failed with exception: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--input-dir", default="notion_markdown", help="Input directory with Notion markdown")
@click.option("--output-dir", default="hugo_markdown", help="Output directory for processed markdown")
@click.option("--portfolio", is_flag=True, help="Configure for portfolio mode (gunn.kim)")
@click.pass_context
def process(ctx, input_dir: str, output_dir: str, portfolio: bool):
    """
    Stage 2: notion_markdown/ → hugo_markdown/
    
    Process Notion markdown for Hugo compatibility and optimization.
    """
    print_info("⚙️  Stage 2: notion_markdown/ → hugo_markdown/")
    
    if ctx.obj.get('dry_run'):
        print_info("🧪 Dry run: Would process markdown for Hugo compatibility")
        return
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        print_error(f"Input directory {input_dir} does not exist")
        print_info("Run 'python -m src notion' first to generate Notion markdown")
        sys.exit(1)
    
    # Ensure output directories exist
    for subdir in ['posts', 'pages']:
        if not ensure_directory(f"{output_dir}/{subdir}"):
            sys.exit(1)
    
    try:
        # Initialize content processor
        processor = ContentProcessor(
            input_dir=input_dir,
            output_dir=output_dir
        )
        
        # Run the processor
        result = processor.run()
        
        if result.get("success"):
            processed_count = result.get("processed_count", 0)
            print_success(f"Stage 2 complete: {processed_count} files processed")
            print_info(f"📁 Output: {output_dir}/")
        else:
            print_error(f"Stage 2 failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Stage 2 failed with exception: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--input-dir", default="hugo_markdown", help="Input directory with processed markdown")
@click.option("--output-dir", default="hugo/content", help="Hugo content directory")
@click.option("--portfolio", is_flag=True, help="Configure for portfolio mode (gunn.kim)")
@click.pass_context
def integrate(ctx, input_dir: str, output_dir: str, portfolio: bool):
    """
    Stage 3: hugo_markdown/ → hugo/content/
    
    Integrate processed markdown into Hugo content structure.
    """
    print_info("🏗️  Stage 3: hugo_markdown/ → hugo/content/")
    
    if ctx.obj.get('dry_run'):
        print_info("🧪 Dry run: Would integrate content into Hugo structure")
        return
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        print_error(f"Input directory {input_dir} does not exist")
        print_info("Run 'python -m src process' first to generate processed markdown")
        sys.exit(1)
    
    # Ensure output directories exist
    if not ensure_directory(f"{output_dir}/posts"):
        sys.exit(1)
    
    try:
        # Initialize Hugo integration
        integration = HugoIntegration(
            input_dir=input_dir,
            output_dir=output_dir
        )
        
        # Run the integration
        result = integration.run()
        
        # Handle both IntegrationResult object and dict results
        if hasattr(result, 'success'):
            # IntegrationResult object
            success = result.success
            integrated_count = result.processed_count
            errors = result.errors
        else:
            # Dict result (fallback)
            success = result.get("success")
            integrated_count = result.get("integrated_count", 0)
            errors = [result.get('error', 'Unknown error')]
        
        if success:
            print_success(f"Stage 3 complete: {integrated_count} files integrated")
            print_info(f"📁 Output: {output_dir}/")
        else:
            if hasattr(result, 'errors') and result.errors:
                for error in result.errors[:3]:  # Show first 3 errors
                    print_error(f"Stage 3 error: {error}")
            else:
                print_error("Stage 3 failed: Unknown error")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Stage 3 failed with exception: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--source-dir", default="hugo", help="Hugo source directory")
@click.option("--output-dir", default="hugo/public", help="Build output directory")
@click.option("--minify", is_flag=True, help="Minify output")
@click.option("--base-url", help="Base URL for the site")
@click.pass_context
def build(ctx, source_dir: str, output_dir: str, minify: bool, base_url: Optional[str]):
    """
    Stage 4: hugo/ → hugo/public/
    
    Build static site using Hugo.
    """
    print_info("🚀 Stage 4: hugo/ → hugo/public/")
    
    if ctx.obj.get('dry_run'):
        print_info("🧪 Dry run: Would build static site with Hugo")
        return
    
    # Validate source directory or fallback
    source_path = Path(source_dir)
    if not source_path.exists() and source_dir == "hugo":
        # Try current directory as fallback (legacy mode)
        source_dir = "."
        print_info("📁 Hugo directory not found, using current directory (legacy mode)")
    
    # Ensure output directory exists
    if not ensure_directory(output_dir):
        sys.exit(1)
    
    try:
        # Initialize build manager
        builder = BuildManager(
            source_dir=source_dir,
            output_dir=output_dir,
            minify=minify,
            base_url=base_url
        )
        
        # Run the build
        result = builder.run()
        
        if result.get("success"):
            file_count = result.get("file_count", 0)
            print_success(f"Stage 4 complete: {file_count} files built")
            print_info(f"📁 Output: {output_dir}/")
            
            # Validate critical files
            index_file = Path(output_dir) / "index.html"
            if index_file.exists():
                size = index_file.stat().st_size
                if size > 100:
                    print_success(f"✅ Site index.html validated ({size} bytes)")
                else:
                    print_warning(f"⚠️  Site index.html seems small ({size} bytes)")
            else:
                print_warning("⚠️  No index.html found in build output")
        else:
            print_error(f"Stage 4 failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Stage 4 failed with exception: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--source-dir", default="hugo/public", help="Built site directory")
@click.option("--target", default="github-pages", help="Deployment target")
@click.option("--prepare", is_flag=True, help="Only prepare deployment artifacts")
@click.pass_context
def deploy(ctx, source_dir: str, target: str, prepare: bool):
    """
    Stage 5: hugo/public/ → hosting
    
    Deploy static site to hosting platform.
    """
    print_info("📦 Stage 5: hugo/public/ → hosting")
    
    if ctx.obj.get('dry_run'):
        print_info(f"🧪 Dry run: Would deploy to {target}")
        return
    
    # Validate source directory
    source_path = Path(source_dir)
    if not source_path.exists():
        print_error(f"Source directory {source_dir} does not exist")
        print_info("Run 'python -m src build' first to generate static site")
        sys.exit(1)
    
    try:
        # Initialize deployment manager
        deployer = DeploymentManager(
            source_dir=source_dir,
            target=target,
            prepare_only=prepare
        )
        
        # Run the deployment
        result = deployer.run()
        
        if result.get("success"):
            if prepare:
                print_success("Stage 5 complete: Deployment artifacts prepared")
            else:
                deployment_url = result.get("url", "N/A")
                print_success(f"Stage 5 complete: Deployed to {target}")
                if deployment_url != "N/A":
                    print_info(f"🌐 Site URL: {deployment_url}")
        else:
            print_error(f"Stage 5 failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Stage 5 failed with exception: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--full", is_flag=True, help="Run all 5 stages")
@click.option("--from-stage", type=int, help="Start from specific stage (1-5)")
@click.option("--to-stage", type=int, help="End at specific stage (1-5)")
@click.pass_context
def run(ctx, full: bool, from_stage: Optional[int], to_stage: Optional[int]):
    """
    Run the complete pipeline or specific stages.
    
    Examples:
        python -m src run --full              # All stages
        python -m src run --from-stage 2      # Stages 2-5
        python -m src run --to-stage 3        # Stages 1-3
        python -m src run --from-stage 2 --to-stage 4  # Stages 2-4
    """
    print_info("🎯 5-Stage Pipeline Execution")
    
    # Determine stage range
    start_stage = from_stage or 1
    end_stage = to_stage or 5
    
    if not full and not from_stage and not to_stage:
        start_stage = 1
        end_stage = 5
        full = True
    
    if start_stage < 1 or start_stage > 5:
        print_error("Start stage must be between 1 and 5")
        sys.exit(1)
    
    if end_stage < 1 or end_stage > 5:
        print_error("End stage must be between 1 and 5")
        sys.exit(1)
    
    if start_stage > end_stage:
        print_error("Start stage cannot be greater than end stage")
        sys.exit(1)
    
    print_info(f"🚀 Running stages {start_stage}-{end_stage}")
    
    # Stage definitions
    stages = [
        (1, "notion", "Notion Database → notion_markdown/"),
        (2, "process", "notion_markdown/ → hugo_markdown/"),
        (3, "integrate", "hugo_markdown/ → hugo/content/"),
        (4, "build", "hugo/ → hugo/public/"),
        (5, "deploy", "hugo/public/ → hosting")
    ]
    
    success_count = 0
    
    try:
        for stage_num, stage_cmd, stage_desc in stages:
            if start_stage <= stage_num <= end_stage:
                print_info(f"▶️  Stage {stage_num}: {stage_desc}")
                
                # Execute stage command
                if stage_cmd == "notion":
                    ctx.invoke(notion)
                elif stage_cmd == "process":
                    ctx.invoke(process)
                elif stage_cmd == "integrate":
                    ctx.invoke(integrate)
                elif stage_cmd == "build":
                    ctx.invoke(build)
                elif stage_cmd == "deploy":
                    ctx.invoke(deploy, prepare=True)  # Only prepare for now
                
                success_count += 1
                print_success(f"✅ Stage {stage_num} completed")
                print()
        
        # Summary
        total_stages = end_stage - start_stage + 1
        print_info(f"📊 Pipeline Summary: {success_count}/{total_stages} stages completed")
        
        if success_count == total_stages:
            print_success("🎉 Pipeline execution completed successfully!")
        else:
            print_warning("⚠️  Some stages may have had issues")
    
    except Exception as e:
        print_error(f"Pipeline execution failed: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def status():
    """Show pipeline status and intermediate storage information."""
    print_info("📊 5-Stage Pipeline Status")
    
    try:
        # Use unified config if available
        if UnifiedConfigLoader is not None:
            config_loader = UnifiedConfigLoader()
            config = config_loader.load_complete_config()
            paths_config = config_loader.get_paths_config()
            
            stages_info = [
                ("Stage 1", paths_config.get("notion_markdown", "notion_markdown"), "Notion markdown files"),
                ("Stage 2", paths_config.get("hugo_markdown", "hugo_markdown"), "Hugo-processed markdown"),
                ("Stage 3", paths_config.get("hugo_content", "hugo/content"), "Hugo content structure"),
                ("Stage 4", paths_config.get("hugo_public", "hugo/public"), "Built static site"),
                ("Stage 5", "deployed", "Deployment status")
            ]
        else:
            # Fallback to default paths
            stages_info = [
                ("Stage 1", "notion_markdown", "Notion markdown files"),
                ("Stage 2", "hugo_markdown", "Hugo-processed markdown"),
                ("Stage 3", "hugo/content", "Hugo content structure"),
                ("Stage 4", "hugo/public", "Built static site"),
                ("Stage 5", "deployed", "Deployment status")
            ]
        
        for stage, directory, description in stages_info:
            path = Path(directory)
            if path.exists():
                if directory.endswith("public"):
                    # Special handling for build output
                    files = list(path.rglob("*"))
                    file_count = len([f for f in files if f.is_file()])
                    status = f"✅ {file_count} files"
                elif stage == "Stage 5":
                    status = "🔍 Check deployment platform"
                else:
                    md_files = list(path.rglob("*.md"))
                    status = f"✅ {len(md_files)} files"
            else:
                status = "❌ Not found"
            
            print_info(f"  {stage}: {status} ({description})")
        
        # Environment status with new variable names
        print_info("\n🔧 Environment Variables:")
        
        if UnifiedConfigLoader is not None:
            config_loader = UnifiedConfigLoader()
            validation = config_loader.validate_complete_pipeline()
            env_status = validation.get("environment_status", {})
            
            required_valid = env_status.get("required_valid", False)
            missing_required = env_status.get("missing_required", [])
            missing_recommended = env_status.get("missing_recommended", [])
            
            print_info(f"  Required Variables: {'✅ All Set' if required_valid else '❌ Missing'}")
            for var in missing_required:
                print_info(f"    ❌ Missing: {var}")
            
            if missing_recommended:
                print_info("  📝 Recommended Variables:")
                for var in missing_recommended:
                    print_info(f"    ⚠️  {var}")
            
            # Show migration status
            migration = env_status.get("migration_report", {})
            if migration.get("legacy_variables_found"):
                print_info("  🔄 Legacy Variables Found:")
                for item in migration["legacy_variables_found"][:3]:
                    print_info(f"    {item['legacy']} → {item['suggested']}")
        else:
            # Fallback environment check
            notion_token = os.environ.get("NOTION_TOKEN")
            database_id = os.environ.get("NOTION_DATABASE_ID") or os.environ.get("NOTION_DATABASE_ID_POSTS")
            
            print_info(f"  NOTION_TOKEN: {'✅ Set' if notion_token else '❌ Not set'}")
            print_info(f"  DATABASE_ID: {'✅ Set' if database_id else '❌ Not set'}")
    
    except Exception as e:
        print_error(f"Status check failed: {e}")
        print_info("Run with --verbose for more details")


@cli.command("config-report")
@click.option("--full", is_flag=True, help="Show full configuration report")
def config_report(full: bool):
    """Show detailed configuration and validation report."""
    if UnifiedConfigLoader is None:
        print_error("Configuration system not available")
        print_info("Please ensure all dependencies are installed")
        return
    
    try:
        config_loader = UnifiedConfigLoader()
        
        if full:
            # Show comprehensive report
            report = config_loader.create_configuration_report()
            print(report)
        else:
            # Show summary
            validation = config_loader.validate_complete_pipeline()
            
            print_info("📋 Configuration Validation Summary")
            print_info("═" * 50)
            
            overall_status = "✅ VALID" if validation["overall_valid"] else "❌ INVALID"
            print_info(f"Overall Status: {overall_status}")
            print()
            
            # Stage results
            print_info("Pipeline Stages:")
            for stage_name, result in validation["stage_results"].items():
                status = "✅" if result["valid"] else "❌"
                print_info(f"  {stage_name.capitalize()}: {status}")
                
                for error in result.get("errors", []):
                    print_error(f"    • {error}")
                
                for warning in result.get("warnings", [])[:2]:  # Show first 2 warnings
                    print_warning(f"    • {warning}")
            
            # Environment summary
            env_status = validation["environment_status"]
            print()
            print_info("Environment Variables:")
            print_info(f"  Required: {'✅' if env_status['required_valid'] else '❌'}")
            
            missing_count = len(env_status.get("missing_required", [])) + len(env_status.get("missing_recommended", []))
            if missing_count > 0:
                print_warning(f"  {missing_count} variables need attention")
            
            # Quick actions
            if not validation["overall_valid"]:
                print()
                print_info("💡 Quick Actions:")
                print_info("  • Set NOTION_TOKEN environment variable")
                print_info("  • Set NOTION_DATABASE_ID for your database")
                print_info("  • Run 'python -m src config-report --full' for details")
            
    except Exception as e:
        print_error(f"Configuration report failed: {e}")
        import traceback
        traceback.print_exc()


@cli.command("create-env")
@click.option("--output", default=".env.example", help="Output file path")
def create_env_template(output: str):
    """Create environment variable template file."""
    try:
        if UnifiedConfigLoader is not None:
            config_loader = UnifiedConfigLoader()
            success = config_loader.env_mapper.create_env_template(output)
            
            if success:
                print_success(f"✅ Environment template created: {output}")
                print_info("Copy to .env and fill in your values")
            else:
                print_error(f"Failed to create template at {output}")
        else:
            # Fallback template creation
            template_content = """# Notion-Hugo Environment Variables
# Copy this file to .env and fill in your actual values

# Required: Notion API Configuration
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here

# Optional: Site Configuration
SITE_TITLE=Your Blog Title
SITE_AUTHOR=Your Name
HUGO_BASE_URL=https://yourdomain.com

# Optional: Deployment
DEPLOY_ENVIRONMENT=production
"""
            with open(output, "w", encoding="utf-8") as f:
                f.write(template_content)
            print_success(f"✅ Basic template created: {output}")
    
    except Exception as e:
        print_error(f"Failed to create environment template: {e}")


if __name__ == "__main__":
    cli()