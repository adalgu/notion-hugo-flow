"""
Real Notion Pipeline Implementation - C1-C3 Components

This module provides production-ready Notion integration:
- C1: NotionAPIClient - API communication with Notion
- C2: MarkdownConverter - Block to Markdown transformation  
- C3: PropertyMapper - Properties to Hugo frontmatter

Stage 1 Output: notion_markdown/ (intermediate storage)
"""

# Import available components
from .property_mapper import PropertyMapper
from .config import NotionConfig

# Import functions from modules (not classes)
from .notion_api import (
    create_notion_client,
    get_database_pages,
    get_page_content,
    get_database_schema
)
from .markdown_converter import (
    convert_rich_text_to_markdown,
    convert_blocks_to_markdown
)

class NotionPipeline:
    """
    Real Notion Pipeline Implementation for Stage 1: Notion Database → notion_markdown/
    
    This class provides production-ready integration with Notion API to:
    - Fetch content from configured Notion databases
    - Convert Notion blocks to clean markdown
    - Generate Hugo-compatible frontmatter
    - Support incremental synchronization
    - Handle API errors and rate limits gracefully
    - Output to notion_markdown/ intermediate storage
    """
    
    def __init__(self, config: dict = None, output_dir: str = "notion_markdown", 
                 state_file: str = "src/config/.notion-hugo-state.json", 
                 incremental: bool = True):
        """
        Initialize NotionPipeline with configuration.
        
        Args:
            config: Pipeline configuration dictionary
            output_dir: Output directory for markdown files
            state_file: Path to state file for incremental sync
            incremental: Enable incremental synchronization
        """
        # Import dependencies with fallbacks
        try:
            from ..metadata import MetadataManager
        except ImportError:
            # Fallback - disable metadata functionality
            MetadataManager = None
            
        try:
            from ..utils.helpers import ensure_directory
        except ImportError:
            # Fallback implementation
            def ensure_directory(path):
                import os
                os.makedirs(path, exist_ok=True)
        from notion_client import Client
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        if config:
            self.config = config
        else:
            try:
                from ..config import load_config
                self.config = load_config()
            except ImportError:
                # Fallback for testing/isolated usage
                self.config = {
                    "mount": {"databases": [], "pages": []},
                    "filename": {}
                }
                print("[Warning] Using fallback configuration - config system not available")
            
        # Validate Notion token
        self.notion_token = os.environ.get("NOTION_TOKEN")
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN environment variable not set")
            
        # Initialize Notion client with API version 2025-09-03
        self.notion = Client(
            auth=self.notion_token,
            notion_version="2025-09-03"
        )
        
        # Pipeline settings
        self.output_dir = output_dir
        self.state_file = state_file
        self.incremental = incremental
        
        # Initialize metadata manager for incremental sync
        if incremental and MetadataManager:
            self.metadata = MetadataManager(state_file)
        else:
            self.metadata = None
            if incremental and not MetadataManager:
                print("[Warning] Metadata system not available - incremental sync disabled")
        
        # Initialize components - use existing function-based modules
        # These will be imported as needed in the processing methods
        
        # Ensure output directories exist
        ensure_directory(f"{output_dir}/posts")
        ensure_directory(f"{output_dir}/pages")
        
        # Pipeline state
        self.processed_count = 0
        self.new_files = 0
        self.updated_files = 0
        self.deleted_files = 0
        self.errors = []
        
    def run(self, **kwargs) -> dict:
        """
        Execute the Notion pipeline to sync content to notion_markdown/.
        
        Returns:
            Dictionary with pipeline execution results
        """
        import time
        from datetime import datetime
        
        print(f"[Info] Starting Notion Pipeline - Mode: {'incremental' if self.incremental else 'full sync'}")
        print(f"[Info] Output directory: {self.output_dir}/")
        
        start_time = time.time()
        
        try:
            # Process databases
            db_results = self._process_databases()
            
            # Process individual pages (if configured)
            page_results = self._process_pages()
            
            # Combine results
            self.processed_count = db_results["processed"] + page_results["processed"]
            self.new_files += db_results["new_files"] + page_results["new_files"]
            self.updated_files += db_results["updated_files"] + page_results["updated_files"]
            self.errors.extend(db_results["errors"] + page_results["errors"])
            
            # Clean up orphaned files
            if self.incremental and self.metadata:
                all_page_ids = db_results["page_ids"] + page_results["page_ids"]
                self.deleted_files = self._cleanup_orphaned_files(all_page_ids)
                
                # Save metadata
                self.metadata.save()
                print(f"[Info] Metadata saved to {self.state_file}")
            
            execution_time = time.time() - start_time
            
            # Print summary
            self._print_summary(execution_time)
            
            return {
                "success": len(self.errors) == 0,
                "file_count": self.processed_count,
                "sync_mode": "incremental" if self.incremental else "full",
                "output_dir": self.output_dir,
                "markdown_files": self._get_output_files(),
                "sync_state": {
                    "processed_count": self.processed_count,
                    "new_files": self.new_files,
                    "updated_files": self.updated_files,
                    "deleted_files": self.deleted_files,
                    "errors": self.errors
                },
                "performance": {
                    "execution_time": execution_time,
                    "api_calls": getattr(self, '_api_calls', 0),
                    "rate_limit_remaining": 100  # TODO: Get from Notion client
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            print(f"[Error] Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_count": self.processed_count,
                "sync_state": {
                    "processed_count": self.processed_count,
                    "new_files": self.new_files,
                    "updated_files": self.updated_files,
                    "deleted_files": self.deleted_files,
                    "errors": self.errors + [str(e)]
                }
            }
    
    def sync_to_markdown(self, **kwargs):
        """
        Legacy method name for backward compatibility.
        Sync Notion content to notion_markdown/ directory.
        """
        return self.run(**kwargs)
    
    def _process_databases(self) -> dict:
        """
        Process all configured Notion databases.
        
        Returns:
            Dictionary with processing results
        """
        from ..utils.helpers import iterate_paginated_api
        from typing import cast
        
        results = {
            "processed": 0,
            "new_files": 0,
            "updated_files": 0,
            "errors": [],
            "page_ids": []
        }
        
        if "mount" not in self.config or "databases" not in self.config["mount"]:
            print("[Info] No databases configured in mount settings")
            return results
        
        print(f"[Info] Processing {len(self.config['mount']['databases'])} configured databases")
        
        for mount in self.config["mount"]["databases"]:
            database_id = mount["database_id"]
            target_folder = mount["target_folder"]
            
            try:
                print(f"[Info] Processing database {database_id} -> {target_folder}/")
                
                # Fetch all pages from database
                all_pages = []
                for page_result in iterate_paginated_api(
                    self.notion.databases.query, 
                    {"database_id": database_id}
                ):
                    page = cast(dict, page_result)
                    if page.get("object") == "page":
                        all_pages.append(page)
                        results["page_ids"].append(page["id"])
                
                # Filter pages for incremental sync
                if self.incremental and self.metadata:
                    pages_to_process = self.metadata.get_changed_pages(all_pages)
                    print(f"[Info] Incremental sync: {len(pages_to_process)}/{len(all_pages)} pages changed")
                else:
                    pages_to_process = all_pages
                    print(f"[Info] Full sync: Processing all {len(pages_to_process)} pages")
                
                # Process each page
                for page in pages_to_process:
                    try:
                        page_result = self._process_single_page(page, target_folder)
                        
                        if page_result["success"]:
                            if page_result["is_new"]:
                                results["new_files"] += 1
                            else:
                                results["updated_files"] += 1
                            results["processed"] += 1
                        else:
                            results["errors"].append({
                                "page_id": page["id"],
                                "error": page_result["error"]
                            })
                            
                    except Exception as e:
                        error_msg = f"Failed to process page {page['id']}: {str(e)}"
                        print(f"[Error] {error_msg}")
                        results["errors"].append({
                            "page_id": page["id"],
                            "error": str(e)
                        })
                        
            except Exception as e:
                error_msg = f"Failed to process database {database_id}: {str(e)}"
                print(f"[Error] {error_msg}")
                results["errors"].append({
                    "database_id": database_id,
                    "error": str(e)
                })
        
        return results
    
    def _process_pages(self) -> dict:
        """
        Process individual configured Notion pages.
        
        Returns:
            Dictionary with processing results
        """
        results = {
            "processed": 0,
            "new_files": 0,
            "updated_files": 0,
            "errors": [],
            "page_ids": []
        }
        
        if "mount" not in self.config or "pages" not in self.config["mount"]:
            print("[Info] No individual pages configured in mount settings")
            return results
        
        print(f"[Info] Processing {len(self.config['mount']['pages'])} configured pages")
        
        for mount in self.config["mount"]["pages"]:
            page_id = mount["page_id"]
            target_folder = mount["target_folder"]
            
            try:
                print(f"[Info] Processing page {page_id} -> {target_folder}/")
                
                # Fetch page
                page = self.notion.pages.retrieve(page_id=page_id)
                results["page_ids"].append(page_id)
                
                # Check if page needs processing (incremental sync)
                if self.incremental and self.metadata:
                    if not self.metadata.has_page_changed(page):
                        print(f"[Info] Page {page_id} unchanged, skipping")
                        continue
                
                # Process page
                page_result = self._process_single_page(page, target_folder)
                
                if page_result["success"]:
                    if page_result["is_new"]:
                        results["new_files"] += 1
                    else:
                        results["updated_files"] += 1
                    results["processed"] += 1
                else:
                    results["errors"].append({
                        "page_id": page_id,
                        "error": page_result["error"]
                    })
                    
            except Exception as e:
                error_msg = f"Failed to process page {page_id}: {str(e)}"
                print(f"[Error] {error_msg}")
                results["errors"].append({
                    "page_id": page_id,
                    "error": str(e)
                })
        
        return results
    
    def _process_single_page(self, page: dict, target_folder: str) -> dict:
        """
        Process a single Notion page to markdown.
        
        Args:
            page: Notion page object
            target_folder: Target subfolder (posts/pages)
            
        Returns:
            Processing result dictionary
        """
        from ..render import get_page_properties, convert_notion_to_markdown
        from ..utils.file_utils import get_filename_with_extension
        import yaml
        import os
        
        page_id = page["id"]
        
        try:
            # Extract page properties
            properties = get_page_properties(page)
            
            # Check if page should be skipped using PropertyMapper
            from .property_mapper import PropertyMapper
            mapper = PropertyMapper()
            if mapper.should_skip_page(properties):
                print(f"[Info] Skipping page {page_id}: skipRendering property set")
                return {"success": True, "is_new": False, "skipped": True}
            
            # Generate frontmatter using PropertyMapper
            frontmatter = mapper.create_hugo_frontmatter(properties, page)
            
            if not frontmatter:
                print(f"[Info] Skipping page {page_id}: empty frontmatter")
                return {"success": True, "is_new": False, "skipped": True}
            
            # Fetch page content blocks
            from ..utils.helpers import iterate_paginated_api
            blocks = list(
                iterate_paginated_api(
                    self.notion.blocks.children.list, 
                    {"block_id": page_id}
                )
            )
            
            # Convert to markdown
            markdown_content = convert_notion_to_markdown(blocks, self.notion)
            
            # Generate filename
            filename = get_filename_with_extension(
                properties, page_id, self.config.get("filename", {})
            )
            
            # Create output file path
            output_path = f"{self.output_dir}/{target_folder}/{filename}"
            
            # Check if file is new
            is_new = not os.path.exists(output_path)
            
            # Create frontmatter YAML
            frontmatter_yaml = yaml.dump(
                frontmatter, default_flow_style=False, allow_unicode=True
            )
            final_content = f"---\n{frontmatter_yaml}---\n\n{markdown_content}"
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            
            # Update metadata
            if self.metadata:
                self.metadata.update_page_status(
                    page_id,
                    status="success",
                    last_edited=page.get("last_edited_time"),
                    target_path=output_path,
                    hash=self.metadata.compute_content_hash(final_content)
                )
            
            print(f"[Info] {'Created' if is_new else 'Updated'}: {output_path}")
            
            return {
                "success": True,
                "is_new": is_new,
                "path": output_path,
                "title": properties.get("title", "Untitled")
            }
            
        except Exception as e:
            # Update metadata with error status
            if self.metadata:
                self.metadata.update_page_status(
                    page_id,
                    status="error",
                    last_edited=page.get("last_edited_time"),
                    error=str(e)
                )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _cleanup_orphaned_files(self, current_page_ids: list) -> int:
        """
        Clean up orphaned files that no longer exist in Notion.
        
        Args:
            current_page_ids: List of currently active page IDs
            
        Returns:
            Number of files deleted
        """
        if not self.metadata:
            return 0
            
        print("[Info] Checking for orphaned files")
        
        # Get orphaned page IDs from metadata
        orphaned_ids = self.metadata.get_orphaned_page_ids(current_page_ids)
        deleted_count = 0
        
        for orphaned_id in orphaned_ids:
            # Get target path from metadata
            page_data = self.metadata.metadata["pages"].get(orphaned_id, {})
            target_path = page_data.get("target_path")
            
            if target_path and os.path.exists(target_path):
                try:
                    os.remove(target_path)
                    print(f"[Info] Deleted orphaned file: {target_path}")
                    deleted_count += 1
                except OSError as e:
                    print(f"[Warning] Failed to delete orphaned file {target_path}: {e}")
            
            # Remove from metadata
            self.metadata.remove_page(orphaned_id)
        
        if deleted_count > 0:
            print(f"[Info] Cleaned up {deleted_count} orphaned files")
        else:
            print("[Info] No orphaned files found")
            
        return deleted_count
    
    def _get_output_files(self) -> list:
        """
        Get list of output markdown files.
        
        Returns:
            List of output file paths
        """
        import glob
        
        files = []
        for pattern in [f"{self.output_dir}/**/*.md"]:
            files.extend(glob.glob(pattern, recursive=True))
        
        return sorted(files)
    
    def _print_summary(self, execution_time: float):
        """
        Print pipeline execution summary.
        
        Args:
            execution_time: Total execution time in seconds
        """
        print("\n=== Notion Pipeline Summary ===")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Mode: {'Incremental' if self.incremental else 'Full sync'}")
        print(f"Output: {self.output_dir}/")
        print(f"Total processed: {self.processed_count}")
        print(f"New files: {self.new_files}")
        print(f"Updated files: {self.updated_files}")
        print(f"Deleted files: {self.deleted_files}")
        print(f"Errors: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors encountered:")
            for i, error in enumerate(self.errors[:5], 1):  # Show first 5 errors
                if isinstance(error, dict):
                    page_id = error.get("page_id", error.get("database_id", "unknown"))
                    print(f"  {i}. {page_id}: {error.get('error', 'Unknown error')}")
                else:
                    print(f"  {i}. {error}")
            
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more errors")
        
        print("=" * 35)

__all__ = [
    "PropertyMapper",
    "NotionConfig", 
    "NotionPipeline",
    # Functions
    "create_notion_client",
    "get_database_pages", 
    "get_page_content",
    "get_database_schema",
    "convert_rich_text_to_markdown",
    "convert_blocks_to_markdown"
]

__version__ = "1.0.0"
