"""
Main Pipeline Orchestrator

Provides unified interface for executing individual pipelines or complete workflows.
This is the main entry point for users to run the entire Notion-Hugo deployment process.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from base_pipeline import StateManager, PipelineResult
from notion.pipeline import NotionPipeline
from hugo.pipeline import HugoPipeline
from deployment.pipeline import DeploymentPipeline


class PipelineOrchestrator:
    """Main orchestrator for running pipelines individually or as a complete workflow"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager()
        
        # Initialize pipelines
        self.notion_pipeline = None
        self.hugo_pipeline = None
        self.deployment_pipeline = None
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config {config_path}: {e}")
            return {}
    
    def initialize_pipelines(self, config_overrides: Dict[str, Any] = None):
        """Initialize all pipelines with their configurations"""
        config_overrides = config_overrides or {}
        
        # Load configurations
        notion_config = self.load_config("notion.yaml")
        hugo_config = self.load_config("hugo.yaml")
        deployment_config = self.load_config("deployment.yaml")
        
        # Apply overrides
        if "notion" in config_overrides:
            notion_config.update(config_overrides["notion"])
        if "hugo" in config_overrides:
            hugo_config.update(config_overrides["hugo"])
        if "deployment" in config_overrides:
            deployment_config.update(config_overrides["deployment"])
        
        # Initialize pipelines
        self.notion_pipeline = NotionPipeline(notion_config.get("notion", {}))
        self.hugo_pipeline = HugoPipeline(hugo_config.get("hugo", {}))
        self.deployment_pipeline = DeploymentPipeline(deployment_config.get("deployment", {}))
        
        self.logger.info("All pipelines initialized successfully")
    
    def run_notion_sync(self, **kwargs) -> PipelineResult:
        """Run Notion sync pipeline"""
        if not self.notion_pipeline:
            raise RuntimeError("Notion pipeline not initialized. Call initialize_pipelines() first.")
        
        self.logger.info("=== Starting Notion Sync Pipeline ===")
        return self.notion_pipeline.run(**kwargs)
    
    def run_hugo_build(self, **kwargs) -> PipelineResult:
        """Run Hugo build pipeline"""
        if not self.hugo_pipeline:
            raise RuntimeError("Hugo pipeline not initialized. Call initialize_pipelines() first.")
        
        self.logger.info("=== Starting Hugo Build Pipeline ===")
        return self.hugo_pipeline.run(**kwargs)
    
    def run_deployment(self, **kwargs) -> PipelineResult:
        """Run deployment pipeline"""
        if not self.deployment_pipeline:
            raise RuntimeError("Deployment pipeline not initialized. Call initialize_pipelines() first.")
        
        self.logger.info("=== Starting Deployment Pipeline ===")
        return self.deployment_pipeline.run(**kwargs)
    
    def run_complete_workflow(self, deploy: bool = True, **kwargs) -> Dict[str, PipelineResult]:
        """Run complete workflow: Notion → Hugo → Deployment"""
        self.logger.info("=== Starting Complete Pipeline Workflow ===")
        
        results = {}
        
        try:
            # Step 1: Notion Sync
            self.logger.info("Step 1/3: Syncing content from Notion...")
            results["notion"] = self.run_notion_sync(**kwargs)
            
            if not results["notion"].success:
                self.logger.error("Notion sync failed. Stopping workflow.")
                return results
            
            # Step 2: Hugo Build
            self.logger.info("Step 2/3: Building Hugo site...")
            results["hugo"] = self.run_hugo_build(**kwargs)
            
            if not results["hugo"].success:
                self.logger.error("Hugo build failed. Stopping workflow.")
                return results
            
            # Step 3: Deployment (optional)
            if deploy:
                self.logger.info("Step 3/3: Deploying site...")
                results["deployment"] = self.run_deployment(**kwargs)
                
                if not results["deployment"].success:
                    self.logger.error("Deployment failed.")
                    return results
            else:
                self.logger.info("Step 3/3: Skipping deployment (deploy=False)")
                results["deployment"] = PipelineResult(
                    success=True,
                    data={"skipped": True},
                    errors=[],
                    duration=0.0,
                    timestamp=datetime.now()
                )
            
            self.logger.info("=== Complete Pipeline Workflow Finished Successfully ===")
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow failed with error: {e}")
            results["error"] = str(e)
            return results
    
    def run_development_workflow(self, **kwargs) -> Dict[str, PipelineResult]:
        """Run development workflow: Notion → Hugo (development build) → Serve"""
        self.logger.info("=== Starting Development Workflow ===")
        
        results = {}
        
        try:
            # Step 1: Notion Sync
            results["notion"] = self.run_notion_sync(**kwargs)
            
            if not results["notion"].success:
                self.logger.error("Notion sync failed. Stopping development workflow.")
                return results
            
            # Step 2: Hugo Development Build
            hugo_kwargs = kwargs.copy()
            hugo_kwargs["build_mode"] = "development"
            results["hugo"] = self.run_hugo_build(**hugo_kwargs)
            
            if not results["hugo"].success:
                self.logger.error("Hugo development build failed.")
                return results
            
            # Note: Hugo serve would be handled separately as it's a long-running process
            self.logger.info("Development build complete. Use 'hugo serve' command to start server.")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Development workflow failed with error: {e}")
            results["error"] = str(e)
            return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of all pipelines"""
        all_states = self.state_manager.get_all_states()
        
        return {
            "notion": all_states.get("notion", {}).to_dict() if all_states.get("notion") else None,
            "hugo": all_states.get("hugo", {}).to_dict() if all_states.get("hugo") else None,
            "deployment": all_states.get("deployment", {}).to_dict() if all_states.get("deployment") else None,
            "last_updated": datetime.now().isoformat()
        }
    
    def validate_setup(self) -> Dict[str, List[str]]:
        """Validate that all pipelines are properly configured"""
        validation_results = {
            "notion": [],
            "hugo": [],
            "deployment": [],
            "general": []
        }
        
        try:
            # Check if Hugo is installed
            import subprocess
            try:
                subprocess.run(["hugo", "version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                validation_results["hugo"].append("Hugo binary not found. Please install Hugo.")
            
            # Check configuration files
            config_files = ["notion.yaml", "hugo.yaml", "deployment.yaml"]
            for config_file in config_files:
                config_path = self.config_dir / config_file
                if not config_path.exists():
                    validation_results["general"].append(f"Configuration file missing: {config_path}")
            
            # Initialize pipelines and validate
            if not validation_results["general"]:  # Only if config files exist
                self.initialize_pipelines()
                
                # Validate individual pipelines
                if self.notion_pipeline:
                    validation_results["notion"] = self.notion_pipeline.notion_config.validate()
                
                if self.hugo_pipeline:
                    validation_results["hugo"] = self.hugo_pipeline.hugo_config.validate()
                
                if self.deployment_pipeline:
                    validation_results["deployment"] = self.deployment_pipeline.deployment_config.validate()
        
        except Exception as e:
            validation_results["general"].append(f"Validation error: {str(e)}")
        
        return validation_results


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Notion-Hugo Pipeline Orchestrator")
    
    # Global options
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--config-dir", type=Path, help="Configuration directory path")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run complete pipeline workflow")
    run_parser.add_argument("--no-deploy", action="store_true", help="Skip deployment step")
    
    # Development command
    dev_parser = subparsers.add_parser("dev", help="Run development workflow")
    
    # Individual pipeline commands
    notion_parser = subparsers.add_parser("notion", help="Run Notion sync only")
    hugo_parser = subparsers.add_parser("hugo", help="Run Hugo build only")
    deploy_parser = subparsers.add_parser("deploy", help="Run deployment only")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show pipeline status")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate pipeline setup")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(args.config_dir)
    
    try:
        if args.command == "run":
            orchestrator.initialize_pipelines()
            results = orchestrator.run_complete_workflow(deploy=not args.no_deploy)
            
            # Print results summary
            print("\n=== Pipeline Workflow Results ===")
            for pipeline, result in results.items():
                if isinstance(result, PipelineResult):
                    status = "✅ SUCCESS" if result.success else "❌ FAILED"
                    print(f"{pipeline.title()}: {status} ({result.duration:.1f}s)")
                    if result.errors:
                        for error in result.errors:
                            print(f"  Error: {error}")
        
        elif args.command == "dev":
            orchestrator.initialize_pipelines()
            results = orchestrator.run_development_workflow()
            print("\n=== Development Workflow Results ===")
            for pipeline, result in results.items():
                if isinstance(result, PipelineResult):
                    status = "✅ SUCCESS" if result.success else "❌ FAILED"
                    print(f"{pipeline.title()}: {status} ({result.duration:.1f}s)")
        
        elif args.command == "notion":
            orchestrator.initialize_pipelines()
            result = orchestrator.run_notion_sync()
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"Notion Sync: {status} ({result.duration:.1f}s)")
        
        elif args.command == "hugo":
            orchestrator.initialize_pipelines()
            result = orchestrator.run_hugo_build()
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"Hugo Build: {status} ({result.duration:.1f}s)")
        
        elif args.command == "deploy":
            orchestrator.initialize_pipelines()
            result = orchestrator.run_deployment()
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"Deployment: {status} ({result.duration:.1f}s)")
        
        elif args.command == "status":
            status = orchestrator.get_pipeline_status()
            print("\n=== Pipeline Status ===")
            for pipeline, state in status.items():
                if state and pipeline != "last_updated":
                    print(f"\n{pipeline.title()}:")
                    print(f"  Status: {state.get('status', 'Unknown')}")
                    print(f"  Last Run: {state.get('last_run', 'Never')}")
                    print(f"  Success: {state.get('last_success', 'Never')}")
        
        elif args.command == "validate":
            validation = orchestrator.validate_setup()
            print("\n=== Pipeline Validation ===")
            
            all_valid = True
            for pipeline, errors in validation.items():
                if errors:
                    all_valid = False
                    print(f"\n{pipeline.title()} Issues:")
                    for error in errors:
                        print(f"  ❌ {error}")
                else:
                    print(f"✅ {pipeline.title()}: OK")
            
            if all_valid:
                print("\n🎉 All pipelines are properly configured!")
            else:
                print("\n⚠️ Please fix the issues above before running pipelines.")
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except Exception as e:
        logging.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()