#!/usr/bin/env python3
"""
Modern CLI entry point for Notion-Hugo Integration.

This application provides a clean, Click-based CLI interface for converting
content from Notion to Hugo-compatible markdown and building Hugo sites.

Core Pipeline (run this first):
    python app.py setup --token YOUR_TOKEN   # Core setup: database + local blog
    python app.py sync                        # Sync from Notion to Hugo
    python app.py build                       # Build Hugo site
    python app.py build --serve               # Build and serve locally

Deployment (optional, after core setup):
    python app.py deploy github              # Deploy to GitHub Pages
    python app.py deploy vercel              # Deploy to Vercel
    python app.py deploy status              # Check deployment status

Utilities:
    python app.py validate                   # Validate current configuration
    python app.py status                     # Show system status
"""

import os
import sys
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

import click

# Get the directory of the current file to handle path resolution correctly
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import existing functionality
from .notion_hugo import (
    run_notion_pipeline,
    run_hugo_pipeline,
    run_setup_database,
    run_migrate_database,
    run_interactive_setup,
    run_quick_setup,
    run_validation,
    validate_hugo_build,
)
from .config import ConfigManager, diagnose_configuration
from .hugo.hugo_setup import HugoSetup, ensure_hugo_setup
from .utils.cli_utils import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    ask_yes_no,
)
from .config.smart_config import SmartConfigManager, ThemeManager
from .utils.config_validator import ConfigValidator, run_validation_check


def run_enhanced_quick_setup(
    target_folder: str = "posts", skip_sample_posts: bool = False
) -> Dict[str, Any]:
    """
    Enhanced quick setup with sample post generation and better error handling.

    Args:
        target_folder: Target folder for content
        skip_sample_posts: Whether to skip generating sample posts

    Returns:
        Setup result dictionary
    """
    try:
        # Use existing quick setup
        result = run_quick_setup(target_folder, skip_sample_posts)

        if result.get("success") and not skip_sample_posts:
            database_id = result.get("database_id")
            if database_id:
                print_info("Generating sample blog posts...")
                sample_result = generate_sample_posts(database_id)
                if sample_result.get("success"):
                    count = sample_result.get("count", 0)
                    method = sample_result.get("method", "unknown")
                    if method == "notion_api":
                        print_success(f"✅ Created {count} sample posts in Notion database")
                    elif method == "local_markdown":
                        print_success(f"✅ Created {count} sample posts as local markdown files")
                        location = sample_result.get("location", "blog/content/posts")
                        print_info(f"📁 Sample files location: {location}")
                        print_info("💡 These posts will appear in your Hugo build")
                    else:
                        print_success(f"✅ Created {count} sample posts")
                else:
                    print_warning("⚠️ Sample post generation failed, but database is ready")
                    print_info("💡 You can create posts manually in your Notion database")

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_sample_posts(database_id: str) -> Dict[str, Any]:
    """
    Generate sample blog posts - fallback to local markdown if API fails.
    
    This function tries to create sample posts in Notion first, but falls back
    to creating local markdown files if the API encounters issues like
    'Nested block depth exceeded' error.

    Args:
        database_id: The database ID to add sample posts to

    Returns:
        Result dictionary with success status and count
    """
    try:
        # First try API creation with minimal structure
        print_info("Attempting to create sample posts in Notion database...")
        return create_simple_notion_samples(database_id)
    except Exception as e:
        error_msg = str(e)
        if "Nested block depth exceeded" in error_msg or "depth" in error_msg.lower():
            print_warning("⚠️ API sample creation failed due to depth limitations...")
            print_info("📝 Falling back to local markdown file creation...")
            return create_local_markdown_samples(database_id)
        elif "Invalid" in error_msg or "Unauthorized" in error_msg:
            print_warning("⚠️ API access issue detected...")
            print_info("📝 Falling back to local markdown file creation...")
            return create_local_markdown_samples(database_id)
        else:
            print_warning(f"⚠️ Unexpected API error: {error_msg}")
            print_info("📝 Falling back to local markdown file creation...")
            return create_local_markdown_samples(database_id)


def create_simple_notion_samples(database_id: str) -> Dict[str, Any]:
    """
    Create very simple Notion samples to avoid depth issues.
    
    This function creates sample posts with minimal structure - no children blocks,
    only the essential properties to avoid triggering Notion API depth limits.

    Args:
        database_id: The database ID to add sample posts to

    Returns:
        Result dictionary with success status and count
    """
    try:
        from notion_client import Client

        notion = Client(
            auth=os.environ.get("NOTION_TOKEN"),
            notion_version="2025-09-03"
        )

        sample_posts = [
            {
                "title": "Welcome to Your New Blog!",
                "description": "Your first sample post to get started with Notion-Hugo",
                "tags": ["Welcome", "Getting Started", "Tutorial"],
            },
            {
                "title": "How to Use Your Notion-Hugo Blog",
                "description": "Learn how to manage your blog with Notion as CMS",
                "tags": ["Tutorial", "Notion", "Workflow"],
            },
        ]

        created_count = 0
        for post_data in sample_posts:
            try:
                # Create a new page with minimal structure - NO children blocks
                new_page = notion.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "Name": {"title": [{"text": {"content": post_data["title"]}}]},
                        "Date": {"date": {"start": datetime.now().isoformat()}},
                        "isPublished": {"checkbox": True},
                        "skipRendering": {"checkbox": False},
                        "Description": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": post_data["description"]
                                    }
                                }
                            ]
                        },
                        "Tags": {
                            "multi_select": [{"name": tag} for tag in post_data["tags"]]
                        },
                        "categories": {"multi_select": [{"name": "Tutorial"}]},
                        "featured": {"checkbox": False},
                        "ShowToc": {"checkbox": True},
                        "HideSummary": {"checkbox": False},
                    }
                    # NO children parameter - this avoids depth issues
                )
                created_count += 1
                print_success(f"✅ Created simple sample post: {post_data['title']}")

            except Exception as e:
                print_warning(
                    f"Failed to create sample post '{post_data['title']}': {str(e)}"
                )
                raise  # Re-raise to trigger fallback

        return {"success": True, "count": created_count, "method": "notion_api"}

    except Exception as e:
        print_warning(f"Simple Notion sample creation failed: {str(e)}")
        raise  # Re-raise to trigger fallback


def create_local_markdown_samples(database_id: str) -> Dict[str, Any]:
    """
    Create sample posts as local markdown files.
    
    This function creates sample blog posts directly as markdown files
    in the content/posts directory, bypassing Notion API limitations.
    This ensures users always get sample content even if API fails.

    Args:
        database_id: The database ID (for reference in frontmatter)

    Returns:
        Result dictionary with success status and count
    """
    try:
        from pathlib import Path
        import os
        from datetime import datetime
        
        # Get correct Hugo content path from ConfigManager
        try:
            config_manager = ConfigManager()
            hugo_content_path = config_manager.get_hugo_content_path()
            content_dir = Path(hugo_content_path) / "posts"
        except Exception:
            # Fallback to blog/content/posts if ConfigManager fails
            content_dir = Path("blog/content/posts")
        
        # Ensure directory exists
        content_dir.mkdir(parents=True, exist_ok=True)
        
        # Sample post data with Hugo frontmatter
        sample_posts = [
            {
                "filename": "welcome-to-your-new-blog.md",
                "title": "Welcome to Your New Blog!",
                "description": "Your first sample post to get started with Notion-Hugo",
                "tags": ["Welcome", "Getting Started", "Tutorial"],
                "content": """# Welcome to Your Notion-Hugo Blog!

🎉 Congratulations! You've successfully set up your Notion-Hugo blog. This is your first sample post to help you get started.

## What you've accomplished:

- ✅ Created a Notion database for your blog posts
- ✅ Set up automatic synchronization with Hugo
- ✅ Configured deployment pipeline
- ✅ Generated sample content (this post!)

## Getting Started:

1. **Edit this post** - Change the title and content to make it your own
2. **Create new posts** - Add new pages to your Notion database
3. **Publish content** - Set the Status to "Published" to make posts live
4. **Customize your site** - Edit the Hugo configuration as needed

## Next Steps:

- Replace this content with your own introduction
- Set up your site's branding and theme
- Start writing amazing content!
- Connect your Notion database for dynamic content

Your blog will automatically sync and deploy when you publish new content in Notion. Happy blogging! 🚀

> **Note**: This sample post was created locally due to API limitations. Once you sync with Notion, you can manage all content through your Notion database."""
            },
            {
                "filename": "how-to-use-your-notion-hugo-blog.md",
                "title": "How to Use Your Notion-Hugo Blog",
                "description": "Learn how to manage your blog with Notion as CMS",
                "tags": ["Tutorial", "Notion", "Workflow"],
                "content": """# Managing Your Blog with Notion

Your blog is now powered by Notion as a CMS and Hugo as a static site generator. Here's how to make the most of it:

## Creating New Posts

1. Open your Notion database
2. Click "New" to create a new page
3. Fill in the title and content
4. Set the Status to "Published" when ready
5. Your blog will automatically update!

## Post Properties

Your database has several properties to help organize your content:

- **Title**: The post title (appears in URLs and headings)
- **Status**: Controls publication (Draft/Published)
- **Tags**: Categorize your content
- **Category**: Group related posts
- **Created**: Automatically tracked
- **Updated**: Shows last modification

## Content Tips

- Use Notion's rich text formatting
- Add images, code blocks, and other media
- Organize content with headings and lists
- Use callouts for important information

## Publishing Workflow

1. Write your post in Notion
2. Review and edit as needed
3. Change Status from "Draft" to "Published"
4. Wait a few minutes for automatic deployment
5. Check your live site!

## Syncing Content

To sync your Notion content: