#!/usr/bin/env python3
"""
Hugo Integration Component for Stage 3 of the Notion-Hugo Pipeline.

This module implements the HugoIntegration class that moves processed markdown files
from the hugo_markdown/ directory to the final Hugo content structure in hugo/content/.

Stage 3: hugo_markdown/posts/ → hugo/content/posts/
         hugo_markdown/pages/ → hugo/content/pages/

Key responsibilities:
- File organization and naming for Hugo compatibility
- Hugo site structure validation
- Conflict detection and resolution
- Support for both copy and symlink strategies
- Comprehensive error handling and logging
"""

import os
import shutil
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

try:
    from ..config import ConfigManager
    from ..utils.file_utils import ensure_directory, safe_filename, calculate_file_hash
    from ..utils.helpers import setup_logging
except ImportError:
    try:
        from src.config import ConfigManager
        from src.utils.file_utils import ensure_directory, safe_filename, calculate_file_hash
        from src.utils.helpers import setup_logging
    except ImportError:
        # Fallback implementations for standalone usage
        ConfigManager = None
        def ensure_directory(path: str) -> None:
            os.makedirs(path, exist_ok=True)
        def safe_filename(name: str) -> str:
            return "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in name).strip()
        def calculate_file_hash(filepath: str) -> str:
            import hashlib
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        def setup_logging(name: str) -> logging.Logger:
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)


@dataclass
class IntegrationConfig:
    """Configuration for Hugo integration operations."""
    strategy: str = "copy"  # "copy" or "symlink"
    preserve_timestamps: bool = True
    conflict_resolution: str = "overwrite"  # "overwrite", "skip", "backup"
    validate_frontmatter: bool = True
    create_index_files: bool = True
    backup_existing: bool = True


@dataclass
class FileOperation:
    """Represents a file operation to be performed."""
    source_path: str
    target_path: str
    operation: str  # "copy", "symlink", "skip"
    reason: str = ""
    conflict: bool = False
    backup_path: Optional[str] = None


@dataclass
class IntegrationResult:
    """Result of Hugo integration operation."""
    success: bool
    processed_count: int
    skipped_count: int
    error_count: int
    operations: List[FileOperation]
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format for CLI compatibility."""
        return {
            "success": self.success,
            "integrated_count": self.processed_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "errors": self.errors,
            "warnings": self.warnings
        }


class HugoIntegration:
    """
    Hugo Integration component for Stage 3 of the pipeline.
    
    Moves processed markdown files from hugo_markdown/ to hugo/content/
    with proper organization and validation.
    """
    
    def __init__(
        self,
        input_dir: str = "hugo_markdown",
        output_dir: str = "hugo/content",
        config: Optional[IntegrationConfig] = None
    ):
        """
        Initialize Hugo integration component.
        
        Args:
            input_dir: Source directory with processed markdown files
            output_dir: Target Hugo content directory
            config: Integration configuration options
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = config or IntegrationConfig()
        self.logger = setup_logging(__name__)
        
        # Load Hugo configuration if available
        self.config_manager = ConfigManager() if ConfigManager else None
        self.hugo_config = self._load_hugo_config()
        
        # Track operations for reporting
        self.operations: List[FileOperation] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _load_hugo_config(self) -> Dict[str, Any]:
        """Load Hugo site configuration."""
        hugo_config = {}
        
        # Try to load from various Hugo config locations
        config_paths = [
            "hugo/config.yaml",
            "hugo/config.yml", 
            "hugo/config.toml",
            "hugo/hugo.yaml",
            "hugo/hugo.yml"
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        if config_path.endswith(('.yaml', '.yml')):
                            hugo_config = yaml.safe_load(f) or {}
                        # Could add TOML support here if needed
                    self.logger.info(f"Loaded Hugo config from {config_path}")
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to load Hugo config from {config_path}: {e}")
        
        return hugo_config
    
    def validate_hugo_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate Hugo site structure and configuration.
        
        Returns:
            Tuple of (is_valid, validation_messages)
        """
        issues = []
        
        # Check if Hugo root exists
        hugo_root = Path("hugo")
        if not hugo_root.exists():
            issues.append("Hugo root directory 'hugo' does not exist")
            return False, issues
        
        # Check essential Hugo files and directories
        required_items = [
            ("hugo/config.yaml", "file", "Hugo configuration file"),
            ("hugo/content", "dir", "Hugo content directory"),
            ("hugo/themes", "dir", "Hugo themes directory"),
        ]
        
        for item_path, item_type, description in required_items:
            path = Path(item_path)
            if item_type == "file" and not path.is_file():
                issues.append(f"Missing {description}: {item_path}")
            elif item_type == "dir" and not path.is_dir():
                issues.append(f"Missing {description}: {item_path}")
        
        # Validate configuration
        if not self.hugo_config:
            issues.append("Could not load Hugo configuration")
        else:
            # Check essential config fields
            if not self.hugo_config.get("title"):
                issues.append("Hugo config missing 'title' field")
            if not self.hugo_config.get("baseURL"):
                issues.append("Hugo config missing 'baseURL' field")
        
        # Check theme
        theme_name = self.hugo_config.get("theme")
        if theme_name:
            theme_path = hugo_root / "themes" / theme_name
            if not theme_path.exists():
                issues.append(f"Theme '{theme_name}' directory not found: {theme_path}")
        
        return len(issues) == 0, issues
    
    def _discover_source_files(self) -> Dict[str, List[Path]]:
        """
        Discover markdown files in the input directory.
        
        Returns:
            Dictionary mapping content types to file lists
        """
        files = {"posts": [], "pages": []}
        
        # Check posts directory
        posts_dir = self.input_dir / "posts"
        if posts_dir.exists():
            for file_path in posts_dir.glob("*.md"):
                if file_path.is_file():
                    files["posts"].append(file_path)
        
        # Check pages directory
        pages_dir = self.input_dir / "pages"
        if pages_dir.exists():
            for file_path in pages_dir.glob("*.md"):
                if file_path.is_file():
                    files["pages"].append(file_path)
        
        self.logger.info(f"Discovered {len(files['posts'])} posts and {len(files['pages'])} pages")
        return files
    
    def _parse_frontmatter(self, file_path: Path) -> Tuple[Dict[str, Any], str]:
        """
        Parse frontmatter and content from markdown file.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Tuple of (frontmatter_dict, content_body)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split frontmatter and content
            parts = content.split('---', 2)
            if len(parts) >= 3 and parts[0].strip() == '':
                # Valid frontmatter format
                frontmatter_text = parts[1]
                body = parts[2].strip()
                
                frontmatter = yaml.safe_load(frontmatter_text) or {}
                return frontmatter, body
            else:
                # No frontmatter
                return {}, content
                
        except Exception as e:
            self.logger.error(f"Failed to parse frontmatter from {file_path}: {e}")
            return {}, ""
    
    def _generate_target_filename(self, source_path: Path, frontmatter: Dict[str, Any]) -> str:
        """
        Generate target filename for Hugo content.
        
        Args:
            source_path: Source file path
            frontmatter: Parsed frontmatter data
            
        Returns:
            Target filename
        """
        # Get date from frontmatter or use current date
        date_str = ""
        if 'date' in frontmatter:
            try:
                # Handle various date formats
                date_value = frontmatter['date']
                if isinstance(date_value, str):
                    # Try parsing ISO format
                    if 'T' in date_value:
                        date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(date_value, '%Y-%m-%d')
                else:
                    date_obj = date_value
                
                date_str = date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                self.logger.warning(f"Could not parse date from frontmatter: {e}")
                date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Get title for filename
        title = frontmatter.get('title', source_path.stem)
        slug = frontmatter.get('slug', safe_filename(title))
        
        # Generate filename based on content type and configuration
        if date_str:
            filename = f"{date_str}-{slug}.md"
        else:
            filename = f"{slug}.md"
        
        return filename
    
    def _determine_target_path(self, source_path: Path, content_type: str) -> Path:
        """
        Determine target path for a source file.
        
        Args:
            source_path: Source file path
            content_type: Content type ("posts" or "pages")
            
        Returns:
            Target file path
        """
        # Parse frontmatter to get metadata
        frontmatter, _ = self._parse_frontmatter(source_path)
        
        # Generate filename
        filename = self._generate_target_filename(source_path, frontmatter)
        
        # Determine target directory
        target_dir = self.output_dir / content_type
        
        return target_dir / filename
    
    def _check_conflicts(self, target_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if target path conflicts with existing files.
        
        Args:
            target_path: Target file path
            
        Returns:
            Tuple of (has_conflict, conflict_reason)
        """
        if not target_path.exists():
            return False, None
        
        return True, f"File already exists: {target_path}"
    
    def _backup_existing_file(self, file_path: Path) -> Optional[Path]:
        """
        Create backup of existing file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file or None if backup failed
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = file_path.with_suffix(f'.{timestamp}.backup')
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to backup file {file_path}: {e}")
            return None
    
    def _perform_file_operation(self, operation: FileOperation) -> bool:
        """
        Perform a single file operation.
        
        Args:
            operation: File operation to perform
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(operation.source_path)
            target_path = Path(operation.target_path)
            
            # Ensure target directory exists
            ensure_directory(str(target_path.parent))
            
            # Handle conflict resolution
            if operation.conflict:
                if self.config.conflict_resolution == "skip":
                    operation.operation = "skip"
                    operation.reason = "Skipped due to conflict and skip policy"
                    return True
                elif self.config.conflict_resolution == "backup":
                    backup_path = self._backup_existing_file(target_path)
                    if backup_path:
                        operation.backup_path = str(backup_path)
                        self.logger.info(f"Backed up existing file to {backup_path}")
            
            # Perform the operation
            if operation.operation == "copy":
                shutil.copy2(source_path, target_path)
                self.logger.info(f"Copied {source_path} → {target_path}")
            elif operation.operation == "symlink":
                # Create relative symlink
                rel_source = os.path.relpath(source_path, target_path.parent)
                if target_path.exists():
                    target_path.unlink()
                target_path.symlink_to(rel_source)
                self.logger.info(f"Linked {source_path} → {target_path}")
            elif operation.operation == "skip":
                self.logger.info(f"Skipped {source_path} → {target_path}: {operation.reason}")
                return True
            
            # Preserve timestamps if configured
            if self.config.preserve_timestamps and operation.operation == "copy":
                stat = source_path.stat()
                os.utime(target_path, (stat.st_atime, stat.st_mtime))
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to perform {operation.operation} operation: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def _plan_operations(self) -> List[FileOperation]:
        """
        Plan all file operations to be performed.
        
        Returns:
            List of planned file operations
        """
        operations = []
        
        # Discover source files
        source_files = self._discover_source_files()
        
        for content_type, files in source_files.items():
            for source_path in files:
                # Determine target path
                target_path = self._determine_target_path(source_path, content_type)
                
                # Check for conflicts
                has_conflict, conflict_reason = self._check_conflicts(target_path)
                
                # Create operation
                operation = FileOperation(
                    source_path=str(source_path),
                    target_path=str(target_path),
                    operation=self.config.strategy,
                    conflict=has_conflict,
                    reason=conflict_reason or ""
                )
                
                operations.append(operation)
        
        return operations
    
    def run(self) -> IntegrationResult:
        """
        Run the Hugo integration process.
        
        Returns:
            Integration result with success status and metrics
        """
        self.logger.info("Starting Hugo integration (Stage 3)")
        
        try:
            # Validate Hugo structure
            is_valid, validation_issues = self.validate_hugo_structure()
            if not is_valid:
                for issue in validation_issues:
                    self.errors.append(issue)
                return IntegrationResult(
                    success=False,
                    processed_count=0,
                    skipped_count=0,
                    error_count=len(self.errors),
                    operations=[],
                    errors=self.errors,
                    warnings=self.warnings
                )
            
            # Check if input directory exists
            if not self.input_dir.exists():
                error_msg = f"Input directory does not exist: {self.input_dir}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                return IntegrationResult(
                    success=False,
                    processed_count=0,
                    skipped_count=0,
                    error_count=1,
                    operations=[],
                    errors=self.errors,
                    warnings=self.warnings
                )
            
            # Plan operations
            self.operations = self._plan_operations()
            
            if not self.operations:
                self.logger.info("No files found to integrate")
                return IntegrationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    operations=[],
                    errors=[],
                    warnings=["No files found to integrate"]
                )
            
            # Execute operations
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for operation in self.operations:
                success = self._perform_file_operation(operation)
                if success:
                    if operation.operation == "skip":
                        skipped_count += 1
                    else:
                        processed_count += 1
                else:
                    error_count += 1
            
            # Determine overall success
            success = error_count == 0
            
            result = IntegrationResult(
                success=success,
                processed_count=processed_count,
                skipped_count=skipped_count,
                error_count=error_count,
                operations=self.operations,
                errors=self.errors,
                warnings=self.warnings
            )
            
            self.logger.info(f"Hugo integration completed: {processed_count} processed, {skipped_count} skipped, {error_count} errors")
            return result
            
        except Exception as e:
            error_msg = f"Hugo integration failed: {e}"
            self.logger.error(error_msg)
            return IntegrationResult(
                success=False,
                processed_count=0,
                skipped_count=0,
                error_count=1,
                operations=[],
                errors=[error_msg],
                warnings=[]
            )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status and configuration.
        
        Returns:
            Status information dictionary
        """
        source_files = self._discover_source_files()
        is_valid, issues = self.validate_hugo_structure()
        
        return {
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "strategy": self.config.strategy,
            "hugo_structure_valid": is_valid,
            "validation_issues": issues,
            "source_files": {
                "posts": len(source_files["posts"]),
                "pages": len(source_files["pages"])
            },
            "hugo_config_loaded": bool(self.hugo_config),
            "theme": self.hugo_config.get("theme", "Not configured")
        }


def main():
    """Command line interface for Hugo integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hugo Integration (Stage 3)")
    parser.add_argument(
        "--input-dir",
        default="hugo_markdown",
        help="Input directory with processed markdown files"
    )
    parser.add_argument(
        "--output-dir", 
        default="hugo/content",
        help="Output directory for Hugo content"
    )
    parser.add_argument(
        "--strategy",
        choices=["copy", "symlink"],
        default="copy",
        help="File operation strategy"
    )
    parser.add_argument(
        "--conflict-resolution",
        choices=["overwrite", "skip", "backup"],
        default="overwrite",
        help="How to handle file conflicts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without performing operations"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = IntegrationConfig(
        strategy=args.strategy,
        conflict_resolution=args.conflict_resolution
    )
    
    # Create integration instance
    integration = HugoIntegration(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config=config
    )
    
    if args.dry_run:
        # Show planned operations
        operations = integration._plan_operations()
        print(f"Would perform {len(operations)} operations:")
        for op in operations:
            print(f"  {op.operation}: {op.source_path} → {op.target_path}")
            if op.conflict:
                print(f"    ⚠️  {op.reason}")
    else:
        # Run integration
        result = integration.run()
        
        if result.success:
            print(f"✅ Integration successful: {result.processed_count} files processed")
        else:
            print(f"❌ Integration failed with {result.error_count} errors")
            for error in result.errors:
                print(f"   Error: {error}")


if __name__ == "__main__":
    main()