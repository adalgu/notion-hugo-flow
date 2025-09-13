#!/usr/bin/env python3
"""
Hugo Content Processor - Stage 2 of the 5-Stage Pipeline

This module implements the real ContentProcessor component for Stage 2 of the pipeline,
processing files from notion_markdown/ to hugo_markdown/ with Hugo-specific optimizations.

Features:
- Incremental processing (only changed files)
- Hugo-specific transformations (shortcodes, image processing)
- Enhanced frontmatter with Hugo-specific fields
- Robust error handling and validation
- Batch and individual file processing
- Comprehensive logging and progress tracking

Usage:
    processor = ContentProcessor(
        input_dir="notion_markdown",
        output_dir="hugo_markdown"
    )
    result = processor.run()
"""

import os
import re
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import yaml
import logging

# Import existing utilities
def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if needed."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

try:
    from ..config import ConfigManager
    from ..notion.markdown_converter import sanitize_filename
except ImportError:
    # Fallback imports for standalone usage
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config.config import ConfigManager
    from notion.markdown_converter import sanitize_filename


class ContentProcessor:
    """
    Hugo Content Processor for Stage 2: notion_markdown/ → hugo_markdown/
    
    This class processes Notion markdown files and optimizes them for Hugo static site generator,
    applying Hugo-specific transformations and enhancements.
    """
    
    def __init__(
        self, 
        input_dir: str = "notion_markdown",
        output_dir: str = "hugo_markdown",
        config_manager: Optional[ConfigManager] = None
    ):
        """
        Initialize the ContentProcessor.
        
        Args:
            input_dir: Directory containing Notion markdown files
            output_dir: Directory for processed Hugo markdown files
            config_manager: Optional ConfigManager instance
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Initialize config manager
        self.config_manager = config_manager or ConfigManager()
        
        # Load configuration
        self.config = self.config_manager.load_config()
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # State file for incremental processing
        self.state_file = Path("src/config/.content-processor-state.json")
        self.state = self._load_state()
        
        # Processing statistics
        self.stats = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the content processor."""
        logger = logging.getLogger("ContentProcessor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_state(self) -> Dict[str, Any]:
        """Load processing state for incremental updates."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}")
        
        return {
            "last_run": None,
            "file_hashes": {},
            "processed_files": []
        }
    
    def _save_state(self) -> None:
        """Save processing state for incremental updates."""
        try:
            # Ensure state directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Update state
            self.state["last_run"] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save state file: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def _should_process_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be processed based on changes.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file should be processed
        """
        file_str = str(file_path)
        current_hash = self._get_file_hash(file_path)
        
        if not current_hash:
            return False
        
        # Check if file is new or changed
        if file_str not in self.state["file_hashes"]:
            return True
        
        return self.state["file_hashes"][file_str] != current_hash
    
    def _discover_files(self) -> List[Path]:
        """
        Discover markdown files that need processing.
        
        Returns:
            List of file paths to process
        """
        files_to_process = []
        
        for subdir in ["posts", "pages"]:
            input_subdir = self.input_dir / subdir
            
            if not input_subdir.exists():
                self.logger.info(f"Input directory {input_subdir} does not exist, skipping")
                continue
            
            # Find all markdown files
            for md_file in input_subdir.glob("*.md"):
                if self._should_process_file(md_file):
                    files_to_process.append(md_file)
                else:
                    self.stats["skipped"] += 1
                    self.logger.debug(f"Skipping unchanged file: {md_file}")
        
        return files_to_process
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content with frontmatter
            
        Returns:
            Tuple of (frontmatter dict, content without frontmatter)
        """
        if not content.startswith('---'):
            return {}, content
        
        try:
            # Find the end of frontmatter
            end_marker = content.find('---', 3)
            if end_marker == -1:
                return {}, content
            
            # Extract and parse frontmatter
            frontmatter_text = content[3:end_marker].strip()
            frontmatter = yaml.safe_load(frontmatter_text) or {}
            
            # Extract content after frontmatter
            markdown_content = content[end_marker + 3:].lstrip()
            
            return frontmatter, markdown_content
            
        except Exception as e:
            self.logger.error(f"Failed to parse frontmatter: {e}")
            return {}, content
    
    def _enhance_frontmatter(self, frontmatter: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Enhance frontmatter with Hugo-specific fields.
        
        Args:
            frontmatter: Original frontmatter
            file_path: Path to the source file
            
        Returns:
            Enhanced frontmatter with Hugo-specific fields
        """
        enhanced = frontmatter.copy()
        
        # Generate slug from filename if not present
        if 'slug' not in enhanced and 'title' in enhanced:
            enhanced['slug'] = sanitize_filename(enhanced['title'])
        
        # Add default weight for ordering
        if 'weight' not in enhanced:
            enhanced['weight'] = 10
        
        # Generate summary from content if not present
        if 'summary' not in enhanced and 'description' not in enhanced:
            # This will be set later when we have the content
            pass
        
        # Set default layout based on content type
        if 'layout' not in enhanced:
            if 'posts' in str(file_path):
                enhanced['layout'] = 'post'
            else:
                enhanced['layout'] = 'page'
        
        # Add Hugo-specific metadata
        enhanced['hugo_processor'] = {
            'version': '2.0.0',
            'processed_at': datetime.now().isoformat(),
            'source_file': str(file_path.relative_to(self.input_dir))
        }
        
        # Add SEO-friendly fields
        if 'title' in enhanced and 'meta_title' not in enhanced:
            enhanced['meta_title'] = enhanced['title']
        
        # Ensure arrays are properly formatted
        for array_field in ['tags', 'categories']:
            if array_field in enhanced and isinstance(enhanced[array_field], str):
                enhanced[array_field] = [tag.strip() for tag in enhanced[array_field].split(',')]
        
        return enhanced
    
    def _transform_markdown_content(self, content: str, frontmatter: Dict[str, Any]) -> str:
        """
        Apply Hugo-specific transformations to markdown content.
        
        Args:
            content: Original markdown content
            frontmatter: Frontmatter for context
            
        Returns:
            Transformed markdown content
        """
        transformed_content = content
        
        # 1. Transform image references to Hugo format
        transformed_content = self._transform_images(transformed_content)
        
        # 2. Transform internal links
        transformed_content = self._transform_links(transformed_content)
        
        # 3. Add Hugo shortcodes for special content
        transformed_content = self._add_hugo_shortcodes(transformed_content)
        
        # 4. Process code blocks for better Hugo compatibility
        transformed_content = self._process_code_blocks(transformed_content)
        
        # 5. Generate summary for frontmatter if needed
        if 'summary' not in frontmatter and 'description' not in frontmatter:
            summary = self._extract_summary(transformed_content)
            if summary:
                frontmatter['summary'] = summary
        
        return transformed_content
    
    def _transform_images(self, content: str) -> str:
        """Transform image references for Hugo compatibility."""
        # Pattern for Markdown images: ![alt](url)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_image(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # If it's a relative path or local file, use Hugo's image processing
            if not image_url.startswith(('http://', 'https://', '//')):
                # Use Hugo's figure shortcode for better control
                return f'{{{{< figure src="{image_url}" alt="{alt_text}" >}}}}'
            
            # Keep external images as-is
            return match.group(0)
        
        return re.sub(image_pattern, replace_image, content)
    
    def _transform_links(self, content: str) -> str:
        """Transform internal links for Hugo compatibility."""
        # Pattern for Markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)
            
            # Transform Notion-style internal links
            if link_url.startswith('notion://') or 'notion.site' in link_url:
                # Convert to Hugo internal link (this would need more sophisticated logic)
                return f'[{link_text}]({{{{< ref "{sanitize_filename(link_text)}" >}}}})'
            
            # Keep external links as-is
            return match.group(0)
        
        return re.sub(link_pattern, replace_link, content)
    
    def _add_hugo_shortcodes(self, content: str) -> str:
        """Add Hugo shortcodes for enhanced functionality."""
        # Convert certain patterns to Hugo shortcodes
        
        # Convert quote blocks to Hugo quote shortcode
        quote_pattern = r'^> (.+)$'
        content = re.sub(quote_pattern, r'{{< quote >}}\1{{< /quote >}}', content, flags=re.MULTILINE)
        
        # Add table of contents shortcode for long content
        if content.count('\n#') >= 3:  # If there are 3 or more headings
            content = '{{< toc >}}\n\n' + content
        
        return content
    
    def _process_code_blocks(self, content: str) -> str:
        """Process code blocks for better Hugo compatibility."""
        # Ensure code blocks have proper language specification
        code_block_pattern = r'```(\w*)\n(.*?)\n```'
        
        def enhance_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            
            # Add line numbers for certain languages
            if language in ['python', 'javascript', 'go', 'java', 'cpp']:
                return f'```{language} {{linenos=true}}\n{code}\n```'
            
            return match.group(0)
        
        return re.sub(code_block_pattern, enhance_code_block, content, flags=re.DOTALL)
    
    def _extract_summary(self, content: str, max_length: int = 150) -> str:
        """Extract summary from content for Hugo frontmatter."""
        # Remove markdown formatting for summary
        summary_text = re.sub(r'[#*`_~\[\]()]', '', content)
        
        # Get first paragraph or first 150 characters
        paragraphs = [p.strip() for p in summary_text.split('\n\n') if p.strip()]
        
        if paragraphs:
            summary = paragraphs[0]
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
            return summary
        
        return ""
    
    def _create_frontmatter_yaml(self, frontmatter: Dict[str, Any]) -> str:
        """Create YAML frontmatter string."""
        return '---\n' + yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True) + '---\n'
    
    def _process_file(self, input_file: Path) -> bool:
        """
        Process a single markdown file.
        
        Args:
            input_file: Path to the input file
            
        Returns:
            True if processing succeeded
        """
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter and content
            frontmatter, markdown_content = self._parse_frontmatter(content)
            
            # Enhance frontmatter
            enhanced_frontmatter = self._enhance_frontmatter(frontmatter, input_file)
            
            # Transform content
            transformed_content = self._transform_markdown_content(markdown_content, enhanced_frontmatter)
            
            # Determine output path
            relative_path = input_file.relative_to(self.input_dir)
            output_file = self.output_dir / relative_path
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write processed file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self._create_frontmatter_yaml(enhanced_frontmatter))
                f.write('\n')
                f.write(transformed_content)
            
            # Update state
            self.state["file_hashes"][str(input_file)] = self._get_file_hash(input_file)
            self.state["processed_files"].append(str(output_file))
            
            self.logger.info(f"Processed: {input_file} → {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process {input_file}: {e}")
            return False
    
    def run(self) -> Dict[str, Any]:
        """
        Run the content processing pipeline.
        
        Returns:
            Dictionary with processing results
        """
        self.logger.info("Starting Hugo content processing (Stage 2)")
        self.stats["start_time"] = datetime.now()
        
        # Ensure output directories exist
        for subdir in ["posts", "pages"]:
            output_subdir = self.output_dir / subdir
            if not ensure_directory(str(output_subdir)):
                self.logger.error(f"Failed to create output directory: {output_subdir}")
                return {
                    "success": False,
                    "error": f"Failed to create output directory: {output_subdir}"
                }
        
        # Discover files to process
        files_to_process = self._discover_files()
        self.logger.info(f"Found {len(files_to_process)} files to process")
        
        if not files_to_process:
            self.logger.info("No files need processing")
            return {
                "success": True,
                "processed_count": 0,
                "message": "No files needed processing"
            }
        
        # Process files
        for file_path in files_to_process:
            if self._process_file(file_path):
                self.stats["processed"] += 1
            else:
                self.stats["errors"] += 1
        
        # Update timing and save state
        self.stats["end_time"] = datetime.now()
        self._save_state()
        
        # Log results
        processing_time = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.logger.info(f"Processing complete in {processing_time:.2f}s")
        self.logger.info(f"Processed: {self.stats['processed']}, Skipped: {self.stats['skipped']}, Errors: {self.stats['errors']}")
        
        return {
            "success": self.stats["errors"] == 0,
            "processed_count": self.stats["processed"],
            "skipped_count": self.stats["skipped"],
            "error_count": self.stats["errors"],
            "processing_time": processing_time,
            "stats": self.stats
        }


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hugo Content Processor - Stage 2")
    parser.add_argument("--input-dir", default="notion_markdown", help="Input directory")
    parser.add_argument("--output-dir", default="hugo_markdown", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger("ContentProcessor").setLevel(logging.DEBUG)
    
    # Run processor
    processor = ContentProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    result = processor.run()
    
    if result["success"]:
        print(f"✅ Content processing completed: {result['processed_count']} files processed")
    else:
        print(f"❌ Content processing failed: {result.get('error', 'Unknown error')}")
        exit(1)


if __name__ == "__main__":
    main()