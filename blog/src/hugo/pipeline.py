"""
Hugo Pipeline Implementation

Handles the building of Hugo static sites from markdown content.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List
import sys
import os

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from base_pipeline import BasePipeline
from .config import HugoConfig


class HugoPipeline(BasePipeline):
    """Pipeline for building Hugo static sites"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("hugo", config)
        self.hugo_config = HugoConfig(config or {})
    
    def validate_inputs(self, **kwargs) -> None:
        """Validate required inputs for Hugo build"""
        content_dir = Path(kwargs.get('content_dir', self.hugo_config.content_dir))
        config_file = Path(kwargs.get('config_file', self.hugo_config.config_file))
        
        if not content_dir.exists():
            raise ValueError(f"Content directory does not exist: {content_dir}")
        
        if not config_file.exists():
            raise ValueError(f"Hugo config file does not exist: {config_file}")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Hugo build pipeline"""
        # Use provided values or fall back to config
        content_dir = Path(kwargs.get('content_dir', self.hugo_config.content_dir))
        config_file = Path(kwargs.get('config_file', self.hugo_config.config_file))
        build_mode = kwargs.get('build_mode', self.hugo_config.build_mode)
        theme = kwargs.get('theme', self.hugo_config.theme)
        output_dir = Path(kwargs.get('output_dir', self.hugo_config.output_dir))
        
        self.logger.info(f"Starting Hugo build - Mode: {build_mode}")
        self.logger.info(f"Content directory: {content_dir}")
        self.logger.info(f"Config file: {config_file}")
        self.logger.info(f"Theme: {theme}")
        self.logger.info(f"Output directory: {output_dir}")
        
        # Build Hugo command
        hugo_cmd = self._build_hugo_command(
            config_file=config_file,
            build_mode=build_mode,
            theme=theme,
            output_dir=output_dir,
            **kwargs
        )
        
        # Execute Hugo build
        build_result = self._execute_hugo_command(hugo_cmd, config_file.parent)
        
        # Analyze build results
        result = self._analyze_build_results(output_dir, build_result)
        
        return result
    
    def _build_hugo_command(self, config_file: Path, build_mode: str, theme: str, 
                           output_dir: Path, **kwargs) -> List[str]:
        """Build the Hugo command with appropriate flags"""
        cmd = ["hugo"]
        
        # Add config file
        cmd.extend(["--config", str(config_file)])
        
        # Add theme
        if theme:
            cmd.extend(["--theme", theme])
        
        # Add destination
        cmd.extend(["--destination", str(output_dir)])
        
        # Build mode specific flags
        if build_mode == "production":
            cmd.append("--minify")
            cmd.append("--gc")  # Enable garbage collection
        elif build_mode == "development":
            cmd.extend(["--buildDrafts", "--buildFuture"])
        
        # Additional options from config
        if self.hugo_config.enable_git_info:
            cmd.append("--enableGitInfo")
        
        if kwargs.get('verbose', False):
            cmd.append("--verbose")
        
        return cmd
    
    def _execute_hugo_command(self, cmd: List[str], work_dir: Path) -> Dict[str, Any]:
        """Execute Hugo command and capture results"""
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            # Change to the Hugo site directory
            original_cwd = os.getcwd()
            os.chdir(work_dir)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.hugo_config.build_timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Hugo build timed out after {self.hugo_config.build_timeout} seconds")
        
        except FileNotFoundError:
            raise RuntimeError("Hugo binary not found. Please install Hugo and ensure it's in your PATH")
        
        finally:
            os.chdir(original_cwd)
    
    def _analyze_build_results(self, output_dir: Path, build_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Hugo build results and gather statistics"""
        if not build_result["success"]:
            # Parse error from stderr
            error_msg = build_result["stderr"] or "Unknown build error"
            raise RuntimeError(f"Hugo build failed: {error_msg}")
        
        # Count generated files
        file_counts = self._count_generated_files(output_dir)
        
        # Parse build info from stdout
        build_info = self._parse_build_info(build_result["stdout"])
        
        return {
            "build_success": True,
            "output_directory": str(output_dir),
            "build_info": build_info,
            "generated_files": file_counts,
            "build_log": {
                "stdout": build_result["stdout"],
                "stderr": build_result["stderr"],
                "command": build_result["command"]
            }
        }
    
    def _count_generated_files(self, output_dir: Path) -> Dict[str, int]:
        """Count generated files by type"""
        if not output_dir.exists():
            return {"total": 0}
        
        file_counts = {
            "html_files": 0,
            "css_files": 0,
            "js_files": 0,
            "images": 0,
            "other_files": 0,
            "total": 0
        }
        
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                file_counts["total"] += 1
                
                suffix = file_path.suffix.lower()
                if suffix in ['.html', '.htm']:
                    file_counts["html_files"] += 1
                elif suffix == '.css':
                    file_counts["css_files"] += 1
                elif suffix in ['.js', '.mjs']:
                    file_counts["js_files"] += 1
                elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                    file_counts["images"] += 1
                else:
                    file_counts["other_files"] += 1
        
        return file_counts
    
    def _parse_build_info(self, stdout: str) -> Dict[str, Any]:
        """Parse build information from Hugo stdout"""
        build_info = {
            "total_pages": 0,
            "total_sections": 0,
            "build_duration": None
        }
        
        # Parse Hugo output for build statistics
        for line in stdout.split('\n'):
            line = line.strip()
            
            # Look for page count
            if "pages created" in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            build_info["total_pages"] = int(part)
                            break
                except (ValueError, IndexError):
                    pass
            
            # Look for build duration
            if "total in" in line.lower():
                try:
                    # Extract duration (e.g., "Total in 123 ms")
                    import re
                    duration_match = re.search(r'total in (\d+)\s*(ms|s)', line.lower())
                    if duration_match:
                        duration_value = int(duration_match.group(1))
                        duration_unit = duration_match.group(2)
                        
                        if duration_unit == 'ms':
                            build_info["build_duration"] = f"{duration_value}ms"
                        else:
                            build_info["build_duration"] = f"{duration_value}s"
                except (ValueError, AttributeError):
                    pass
        
        return build_info
    
    def validate_outputs(self, result_data: Dict[str, Any]) -> None:
        """Validate pipeline outputs"""
        required_keys = ['build_success', 'output_directory', 'generated_files']
        
        for key in required_keys:
            if key not in result_data:
                raise ValueError(f"Required output key '{key}' missing from result")
        
        if not result_data['build_success']:
            raise ValueError("Hugo build was not successful")
        
        output_dir = Path(result_data['output_directory'])
        if not output_dir.exists():
            raise ValueError(f"Output directory was not created: {output_dir}")
    
    def build_production(self, **kwargs) -> Dict[str, Any]:
        """Build for production deployment"""
        return self.run(build_mode="production", **kwargs)
    
    def build_development(self, **kwargs) -> Dict[str, Any]:
        """Build for development"""
        return self.run(build_mode="development", **kwargs)
    
    def serve(self, **kwargs) -> Dict[str, Any]:
        """Start Hugo development server"""
        # TODO: Implement Hugo serve functionality
        raise NotImplementedError("Hugo serve functionality not yet implemented")