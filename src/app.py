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

```bash
python app.py sync
```

To build and serve locally:

```bash
python app.py build --serve
```

Your blog is now ready for amazing content! 📝

> **Tip**: This sample post demonstrates various markdown features. Edit or delete it once you're comfortable with the workflow."""
            }
        ]
        
        created_count = 0
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for post_data in sample_posts:
            try:
                filename = f"{current_date}-{post_data['filename']}"
                file_path = content_dir / filename
                
                # Skip if file already exists
                if file_path.exists():
                    print_info(f"📄 Sample post already exists: {filename}")
                    created_count += 1
                    continue
                
                # Create Hugo frontmatter
                frontmatter = f"""---
title: "{post_data['title']}"
date: {current_date}T{datetime.now().strftime('%H:%M:%S')}+09:00
draft: false
description: "{post_data['description']}"
tags: {post_data['tags']}
categories: ["Tutorial"]
showToc: true
hideSummary: false
# Notion reference
notion_database_id: "{database_id}"
created_method: "local_fallback"
---

"""
                
                # Write the complete markdown file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(frontmatter + post_data["content"])
                
                created_count += 1
                print_success(f"✅ Created local sample post: {filename}")
                
            except Exception as e:
                print_warning(
                    f"Failed to create local sample post '{post_data['filename']}': {str(e)}"
                )
        
        if created_count > 0:
            print_info(f"📁 Sample posts created in: {content_dir.absolute()}")
            print_info("🔄 Run 'python app.py build' to see them in your site")
        
        return {
            "success": True, 
            "count": created_count, 
            "method": "local_markdown",
            "location": str(content_dir.absolute())
        }
    
    except Exception as e:
        print_error(f"Local markdown sample creation failed: {str(e)}")
        return {"success": False, "error": str(e), "method": "local_markdown"}


def setup_configuration(
    token: str, database_id: str, target_folder: str
) -> Dict[str, Any]:
    """
    Set up configuration files and environment variables.

    Args:
        token: Notion API token
        database_id: Database ID for posts
        target_folder: Target folder for content

    Returns:
        Configuration result dictionary
    """
    try:
        # Create or update .env file
        env_content = f"""# Notion-Hugo Configuration
# Your Notion API token (keep this secure!)
NOTION_TOKEN={token}

# Database ID for your blog posts
# This is automatically set during setup
NOTION_DATABASE_ID_POSTS={database_id}

# Optional: Additional settings
# NOTION_PAGE_ID_ABOUT=your_about_page_id_here
# HUGO_BASE_URL=https://your-domain.com
# GA_ID=your_google_analytics_id
"""

        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)

        print_info("✅ Created .env file with your configuration")
        print_info(f"📋 Database ID saved: {database_id[:8]}...")

        # Update config.yaml with the database ID
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config()

            # Ensure the structure exists
            if "notion" not in config:
                config["notion"] = {}
            if "mount" not in config["notion"]:
                config["notion"]["mount"] = {}
            if "databases" not in config["notion"]["mount"]:
                config["notion"]["mount"]["databases"] = []

            # Update the database configuration
            if config["notion"]["mount"]["databases"]:
                config["notion"]["mount"]["databases"][0]["database_id"] = database_id
                config["notion"]["mount"]["databases"][0][
                    "target_folder"
                ] = target_folder
            else:
                config["notion"]["mount"]["databases"] = [
                    {
                        "database_id": database_id,
                        "target_folder": target_folder,
                        "content_type": "post",
                    }
                ]

            config_manager.save_config(config)
            print_info("✅ Updated config.yaml with database settings")

            # Show configuration summary
            print_info("\n📋 Configuration Summary:")
            print_info(f"   • Database ID: {database_id}")
            print_info(f"   • Target folder: {target_folder}")
            print_info(f"   • Config file: notion-hugo.config.yaml")
            print_info(f"   • Environment file: .env")

        except Exception as e:
            print_warning(f"⚠️  Could not update config.yaml: {str(e)}")
            print_info("You may need to manually configure the database ID")
            return {"success": False, "error": f"Config update failed: {str(e)}"}

        # Create .gitignore if it doesn't exist
        gitignore_path = Path(".gitignore")
        if not gitignore_path.exists():
            gitignore_content = """# Notion-Hugo specific
.env
.env.local
.env.production
*.log
.DS_Store

# Hugo
public/
resources/
.hugo_build.lock

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
Thumbs.db
"""
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(gitignore_content)
            print_info("✅ Created .gitignore file to protect sensitive data")

        # Ensure Hugo site setup
        print_info("🏗️ Setting up Hugo site structure...")
        try:
            config_manager = ConfigManager()
            if ensure_hugo_setup(config_manager):
                print_info("✅ Hugo site structure ready")
            else:
                print_warning("⚠️  Hugo site setup had issues, but continuing...")
        except Exception as e:
            print_warning(f"⚠️  Hugo setup failed: {str(e)}")
            print_info(
                "Continuing without Hugo setup - you may need to initialize manually"
            )

        # Validate the configuration
        try:
            from notion_client import Client

            notion = Client(
                auth=token,
                notion_version="2025-09-03"
            )

            # Test database access
            database = notion.databases.retrieve(database_id=database_id)
            print_info("✅ Database configuration validated successfully")
            print_info(
                f"📋 Database title: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}"
            )

        except Exception as e:
            print_warning(f"⚠️  Database validation failed: {str(e)}")
            print_info(
                "The configuration was saved, but you may need to check database permissions"
            )
            return {"success": False, "error": f"Database validation failed: {str(e)}"}

        return {"success": True, "database_id": database_id}

    except Exception as e:
        print_error(f"Configuration setup failed: {str(e)}")
        return {"success": False, "error": str(e)}


def setup_github_integration(token: str, database_id: str) -> Dict[str, Any]:
    """
    Set up GitHub repository and deployment integration.

    Args:
        token: Notion API token
        database_id: Database ID for posts

    Returns:
        GitHub setup result dictionary
    """
    try:
        import subprocess
        from subprocess import TimeoutExpired

        # Check if we're in a git repository
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"], check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            print_info("Initializing git repository...")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Notion-Hugo blog setup"],
                check=True,
            )

        # Check if GitHub CLI is available
        try:
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("GitHub CLI not found. Manual setup required.")
            _print_manual_github_setup_instructions()
            return {
                "success": False,
                "error": "GitHub CLI not available",
                "manual_setup": True,
            }

        # Check if user is authenticated
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError:
            print_warning("Not authenticated with GitHub CLI.")
            print_info("Run 'gh auth login' then re-run setup")
            _print_manual_github_setup_instructions()
            return {
                "success": False,
                "error": "GitHub authentication required",
                "manual_setup": True,
            }

        # Try to run the GitHub setup script with timeout
        script_path = "./dev/scripts/github-pages-setup.sh"
        if os.path.exists(script_path):
            print_info("Running GitHub Pages setup script...")
            print_warning(
                "This may take up to 60 seconds. If it hangs, we'll provide manual instructions."
            )

            # Set environment variables for the script (make it non-interactive)
            env = os.environ.copy()
            env["NOTION_TOKEN"] = token
            env["NOTION_DATABASE_ID_POSTS"] = database_id
            # Add environment variables to make script non-interactive
            env["NON_INTERACTIVE"] = "true"
            env["AUTO_CONFIRM"] = "yes"  # Auto-answer 'yes' to prompts
            env["FORCE_PUSH"] = "no"  # Don't force push by default

            try:
                # Use a more generous timeout for the GitHub script
                result = subprocess.run(
                    ["bash", script_path],
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60 second timeout to prevent hanging
                )

                # Try to extract repository URL from git remote
                try:
                    repo_result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    repo_url = repo_result.stdout.strip()
                    print_success(f"GitHub setup completed successfully: {repo_url}")
                    return {"success": True, "repo_url": repo_url}
                except subprocess.CalledProcessError:
                    print_success("GitHub setup completed successfully")
                    return {"success": True, "repo_url": "Repository configured"}

            except TimeoutExpired:
                print_warning("GitHub setup script timed out after 60 seconds.")
                print_info(
                    "This usually happens when the script encounters interactive prompts."
                )
                print_info("Your repository may have been partially configured.")
                _print_manual_github_setup_instructions()
                return {
                    "success": False,
                    "error": "Script timeout - manual setup required",
                    "manual_setup": True,
                }
            except subprocess.CalledProcessError as e:
                print_warning(
                    f"GitHub setup script failed with exit code {e.returncode}"
                )
                if e.stdout:
                    print_info(f"Script output: {e.stdout.strip()}")
                if e.stderr:
                    print_warning(f"Script errors: {e.stderr.strip()}")

                # Check if it's a recoverable error
                if "auth" in str(e).lower() or "login" in str(e).lower():
                    print_warning("GitHub authentication issue detected.")
                elif "permission" in str(e).lower() or "access" in str(e).lower():
                    print_warning("GitHub permission issue detected.")
                else:
                    print_warning("Unknown GitHub setup error occurred.")

                _print_manual_github_setup_instructions()
                return {
                    "success": False,
                    "error": f"Exit code {e.returncode}: {str(e)}",
                    "manual_setup": True,
                }
        else:
            print_warning(f"GitHub setup script not found at {script_path}")
            _print_manual_github_setup_instructions()
            return {
                "success": False,
                "error": "Setup script not found",
                "manual_setup": True,
            }

    except Exception as e:
        print_error(f"GitHub integration failed with unexpected error: {str(e)}")
        _print_manual_github_setup_instructions()
        return {"success": False, "error": str(e), "manual_setup": True}


def _print_manual_github_setup_instructions() -> None:
    """
    Print detailed instructions for manual GitHub setup when automatic setup fails.
    """
    print_info("\n📋 Manual GitHub Setup Instructions")
    print_info("━" * 50)

    print_info("\n🔐 Step 1: Install and authenticate GitHub CLI")
    print_info("   • Install GitHub CLI: https://cli.github.com/manual/installation")
    print_info("   • Authenticate with GitHub:")
    print_info("     gh auth login")
    print_info("   • Verify authentication:")
    print_info("     gh auth status")

    print_info("\n🏗️  Step 2: Create and configure repository")
    print_info("   • Create your GitHub Pages repository:")
    print_info("     gh repo create YOUR-USERNAME.github.io --public")
    print_info("   • Add remote origin:")
    print_info(
        "     git remote add origin https://github.com/YOUR-USERNAME/YOUR-USERNAME.github.io.git"
    )
    print_info("   • Push your code:")
    print_info("     git push -u origin main")

    print_info("\n🔑 Step 3: Set up GitHub secrets")
    print_info("   • Get your Notion token from .env file or environment")
    print_info("   • Set the secret (replace with your actual token):")
    print_info("     gh secret set NOTION_TOKEN --body 'YOUR_NOTION_TOKEN'")

    print_info("\n📄 Step 4: Enable GitHub Pages")
    print_info("   • Go to your repository settings:")
    print_info(
        "     https://github.com/YOUR-USERNAME/YOUR-USERNAME.github.io/settings/pages"
    )
    print_info("   • Under 'Build and deployment', select 'GitHub Actions' as source")
    print_info("   • Save the settings")

    print_info("\n🚀 Step 5: Deploy your site")
    print_info("   • Trigger the deployment workflow:")
    print_info("     gh workflow run 'Deploy Hugo site to Pages'")
    print_info("   • Monitor workflow progress:")
    print_info("     gh run list")
    print_info("   • Check your live site at:")
    print_info("     https://YOUR-USERNAME.github.io")

    print_info("\n🛠️  Alternative: Run the setup script manually")
    print_info("   • If you want to retry the automated setup later:")
    print_info("     ./dev/scripts/github-pages-setup.sh")
    print_info("   • Or with environment variables for non-interactive mode:")
    print_info(
        "     NON_INTERACTIVE=true AUTO_CONFIRM=yes ./dev/scripts/github-pages-setup.sh"
    )

    print_info("\n💡 Tips:")
    print_info("   • Replace 'YOUR-USERNAME' with your actual GitHub username")
    print_info("   • Check .env file for your NOTION_TOKEN value")
    print_info("   • Deployment may take 5-10 minutes after workflow completion")
    print_info("━" * 50)


def finalize_deployment(skip_github: bool) -> Dict[str, Any]:
    """
    Finalize the deployment process.

    Args:
        skip_github: Whether GitHub setup was skipped

    Returns:
        Deployment finalization result
    """
    try:
        # Check if public directory exists and has content
        public_dir = Path("public")
        if public_dir.exists() and any(public_dir.iterdir()):
            print_info("Hugo build output verified")

            # Check for index.html
            index_file = public_dir / "index.html"
            if index_file.exists():
                file_size = index_file.stat().st_size
                print_info(f"Site index.html: {file_size} bytes")

                if file_size > 100:
                    print_success("Site appears to be built correctly")
                else:
                    print_warning(
                        "Site index.html seems too small - may be an error page"
                    )
            else:
                print_warning("No index.html found in build output")
        else:
            print_warning("No Hugo build output found")

        # If GitHub setup was not skipped, check repository status
        if not skip_github:
            try:
                import subprocess
                from subprocess import TimeoutExpired

                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                repo_url = result.stdout.strip()
                print_info(f"Repository: {repo_url}")

                # Check if we can push (has commits to push)
                try:
                    subprocess.run(["git", "push"], check=True, capture_output=True)
                    print_info("Successfully pushed to GitHub")
                except subprocess.CalledProcessError:
                    print_info("No new commits to push")

            except subprocess.CalledProcessError:
                print_warning("Repository not configured or not connected to GitHub")

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


class NotionHugoApp:
    """Main application class for Notion-Hugo CLI."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.config_manager = ConfigManager()
        self._setup_signal_handlers()
        load_dotenv()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def handle_signal(sig: int, frame) -> None:  # type: ignore[no-untyped-def]
            print_warning("\nReceived interrupt signal. Shutting down...")
            sys.exit(130)  # Standard exit code for SIGINT

        signal.signal(signal.SIGINT, handle_signal)

    def validate_environment(self) -> bool:
        """Validate the current environment setup."""
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            print_error("NOTION_TOKEN environment variable is not set")
            print_info("Please run 'python app.py setup --token YOUR_TOKEN' first")
            return False

        return True


# Create application instance
app = NotionHugoApp()


@click.group(invoke_without_command=True)
@click.option("--token", help="Notion API token (auto-triggers setup)")
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx: click.Context, token: Optional[str], version: bool) -> None:
    """
    Notion-Hugo Integration CLI - Modern blog publishing with Notion as CMS.

    Convert Notion pages to Hugo markdown and deploy static sites automatically.
    Perfect for developers who want to use Notion as their blog CMS.

    Quick start:
        python app.py --token YOUR_NOTION_TOKEN    # Auto setup with token
        python app.py                              # Interactive setup
    """
    if version:
        click.echo("Notion-Hugo CLI v1.0.0")
        return

    if ctx.invoked_subcommand is None:
        # No subcommand provided
        if token:
            # Token provided - start automatic setup
            print_info("🚀 Token provided - starting automatic setup...")
            ctx.invoke(setup, token=token)
            return
        else:
            # No token - start interactive setup
            print_header("🚀 Welcome to Notion-Hugo!")
            print_info("Let's get your blog set up in just a few minutes.")
            print_info("We'll guide you through the process step by step.")
            print()

            # Interactive token input
            token_input = None
            while not token_input:
                try:
                    print_info("First, we need your Notion API token.")
                    print_info(
                        "📚 Don't have one? Get it here: https://www.notion.so/my-integrations"
                    )
                    print()

                    token_input = input("🔑 Enter your Notion API token: ").strip()

                    if not token_input:
                        print_warning("Token cannot be empty. Please try again.")
                        continue

                    if not token_input.startswith(("ntn_", "secret_")):
                        print_warning("⚠️ Token should start with 'ntn_' or 'secret_'")
                        retry = input("Continue anyway? (y/n): ").lower().strip()
                        if retry not in ["y", "yes"]:
                            token_input = None
                            continue

                    break

                except KeyboardInterrupt:
                    print_info("\n🛑 Setup cancelled by user")
                    ctx.exit(130)
                except EOFError:
                    print_info("\n🛑 Setup cancelled by user")
                    ctx.exit(130)

            # Start setup with the provided token
            print_info("✅ Token received - starting setup...")
            ctx.invoke(setup, token=token_input)
            return


@cli.command()
@click.option(
    "--token",
    required=True,
    help="Notion API token (starts with 'ntn_')",
    prompt="Enter your Notion API token",
)
@click.option(
    "--target-folder",
    default="posts",
    help="Target folder for content (default: posts)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Run interactive setup instead of quick setup",
)
@click.option(
    "--database-id",
    help="Use existing Database ID or Page ID with database blocks (instead of creating new one)",
)
@click.option("--migrate-from", help="Database ID to migrate from (optional)")
@click.option("--skip-sample-posts", is_flag=True, help="Skip sample post generation")
def setup(
    token: str,
    target_folder: str,
    interactive: bool,
    database_id: Optional[str],
    migrate_from: Optional[str],
    skip_sample_posts: bool,
) -> None:
    """
    Core Notion-Hugo setup - Get your blog running locally in minutes.

    This command will:
    \b
    1. ✅ Validate your Notion API token
    2. ✅ Create a new Notion database (or migrate existing one)
    3. ✅ Generate sample blog posts (unless --skip-sample-posts)
    4. ✅ Configure environment variables (.env, config.yaml)
    5. ✅ Run initial content sync (Notion → Hugo markdown)
    6. ✅ Build Hugo static site
    7. ✅ Serve locally + show preview URL
    8. ✅ Success confirmation with clear next steps

    For deployment, use separate commands:
        python app.py deploy github    # Set up GitHub Pages
        python app.py deploy vercel    # Set up Vercel
        python app.py deploy status    # Check deployment status

    Examples:
        python app.py setup --token YOUR_NOTION_TOKEN
        python app.py setup --token YOUR_NOTION_TOKEN --interactive
        python app.py setup --token YOUR_NOTION_TOKEN --database-id EXISTING_DB_ID
        python app.py setup --token YOUR_NOTION_TOKEN --migrate-from OLD_DB_ID
    """
    print_header("🚀 Notion-Hugo 5-Minute Setup")
    print_info("Welcome! Let's get your blog up and running in just 5 minutes.")
    print_info("From Notion token to live blog in one command!")

    # Set environment variable for the session
    os.environ["NOTION_TOKEN"] = token

    setup_progress = {
        "total_steps": 7,
        "current_step": 0,
        "success_steps": [],
        "failed_steps": [],
    }

    def update_progress(step_name: str, success: bool = True) -> None:
        setup_progress["current_step"] += 1
        if success:
            setup_progress["success_steps"].append(step_name)
            print_success(
                f"✅ Step {setup_progress['current_step']}/{setup_progress['total_steps']}: {step_name}"
            )
        else:
            setup_progress["failed_steps"].append(step_name)
            print_error(
                f"❌ Step {setup_progress['current_step']}/{setup_progress['total_steps']}: {step_name}"
            )

        # Progress bar
        progress = setup_progress["current_step"] / setup_progress["total_steps"]
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print_info(f"Progress: [{bar}] {progress:.0%}")
        print()

    try:
        # Step 1: Validate Notion token and permissions
        print_info("🔐 Step 1/7: Validating Notion API token and permissions...")
        try:
            from notion_client import Client

            notion = Client(
                auth=token,
                notion_version="2025-09-03"
            )

            # Test the token by trying to list users (this requires basic permissions)
            try:
                notion.users.list()
                update_progress("Notion token validation")
            except Exception as e:
                if "Unauthorized" in str(e) or "Invalid token" in str(e):
                    print_error(
                        "Invalid Notion token. Please check your token and try again."
                    )
                    print_info("To get your token:")
                    print_info("1. Go to https://www.notion.so/my-integrations")
                    print_info("2. Create a new integration or use an existing one")
                    print_info("3. Copy the 'Internal Integration Token'")
                    sys.exit(1)
                else:
                    print_warning(f"Token validation warning: {str(e)}")
                    print_info("Continuing with setup - token appears to be valid")
                    update_progress("Notion token validation (with warnings)")
        except Exception as e:
            update_progress("Notion token validation", False)
            print_error(f"Failed to validate token: {str(e)}")
            sys.exit(1)

        # Step 2: Create or migrate Notion database
        print_info("📊 Step 2/7: Setting up Notion database...")

        # Determine scenario and show appropriate guide
        if not token:
            print_info("🎯 Demo Mode: Starting with sample content")
            print_info("• You'll see a sample blog to understand the structure")
            print_info(
                "• Run 'python app.py setup --token YOUR_TOKEN' to connect with Notion"
            )
        elif token and not database_id:
            print_info("🚀 New User Mode: Creating optimized database")
            print_info("• A new database will be created with the perfect structure")
            print_info("• Sample posts will be generated for you")
        elif token and database_id:
            print_info("📊 Existing Database Mode: Connecting to your database")
            print_info("• We'll validate and optimize your existing database")
            print_info("• Your data will be preserved")

        try:
            if database_id:
                # Use existing Database ID or Page ID
                print_info(f"Using provided ID: {database_id}")

                # Smart validation: Check if it's a database or a page
                try:
                    # First, try to retrieve as database
                    try:
                        database = notion.databases.retrieve(database_id=database_id)
                        result = {"success": True, "database_id": database_id}
                        update_progress(
                            f"Database validation (ID: {database_id[:8]}...)"
                        )
                        print_info("✅ Valid Database ID - contains database blocks")
                        print_info(
                            f"📋 Database title: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}"
                        )

                        # Check database structure for compatibility
                        properties = database.get("properties", {})
                        required_props = ["Name", "Status", "Tags", "Category"]
                        missing_props = [
                            prop for prop in required_props if prop not in properties
                        ]

                        if missing_props:
                            print_warning(
                                f"⚠️ Database missing recommended properties: {', '.join(missing_props)}"
                            )
                            print_info(
                                "🔧 Would you like to automatically add missing properties?"
                            )
                            response = (
                                input("Add missing properties? (y/n): ").lower().strip()
                            )
                            if response in ["y", "yes"]:
                                print_info(
                                    "🔄 Adding missing properties to database..."
                                )
                                updates = {}
                                for prop in missing_props:
                                    if prop == "Name":
                                        updates[prop] = {"title": {}}
                                    elif prop == "Status":
                                        updates[prop] = {
                                            "select": {
                                                "options": [
                                                    {"name": "Draft", "color": "gray"},
                                                    {
                                                        "name": "Published",
                                                        "color": "green",
                                                    },
                                                ]
                                            }
                                        }
                                    elif prop == "Tags":
                                        updates[prop] = {"multi_select": {}}
                                    elif prop == "Category":
                                        updates[prop] = {
                                            "select": {
                                                "options": [
                                                    {"name": "Tech", "color": "blue"},
                                                    {"name": "Life", "color": "green"},
                                                    {
                                                        "name": "Tutorial",
                                                        "color": "orange",
                                                    },
                                                ]
                                            }
                                        }

                                notion.databases.update(
                                    database_id=database_id, properties=updates
                                )
                                print_success(
                                    f"✅ Added properties: {', '.join(updates.keys())}"
                                )
                            else:
                                print_info(
                                    "ℹ️ You can manually add properties later in Notion"
                                )

                    except Exception as db_error:
                        # If database retrieval fails, try as page
                        try:
                            page = notion.pages.retrieve(page_id=database_id)
                            print_info(
                                f"📋 Page title: {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}"
                            )

                            # Check if page contains database blocks
                            if page.get("properties") and any(
                                prop.get("type") == "database"
                                for prop in page.get("properties", {}).values()
                            ):
                                result = {"success": True, "database_id": database_id}
                                update_progress(
                                    f"Page with database validation (ID: {database_id[:8]}...)"
                                )
                                print_info(
                                    "✅ Valid Page ID - contains database blocks"
                                )
                                print_info(
                                    f"📋 Page title: {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}"
                                )
                            else:
                                # It's a regular page, not a database
                                update_progress("Page validation", False)
                                print_error(
                                    f"ID {database_id[:8]}... is a regular page, not a database"
                                )
                                print_info(
                                    "This ID points to a regular page without database blocks"
                                )
                                print_info("🔧 Quick fixes you can try:")
                                print_info("   1. Create a database in that page:")
                                print_info("      • Open the page in Notion")
                                print_info(
                                    "      • Type '/' and select 'Table' or 'Database'"
                                )
                                print_info("      • Use the new database ID")
                                print_info(
                                    "   2. Use a different page that contains a database"
                                )
                                print_info(
                                    "   3. Run without --database-id to create a new database"
                                )
                                print_info("   4. Use --interactive for guided setup")

                                # Offer to help create a database in the page
                                try:
                                    import subprocess
                                    import sys

                                    response = (
                                        input(
                                            "\n🤔 Would you like to create a database in this page? (y/n): "
                                        )
                                        .lower()
                                        .strip()
                                    )
                                    if response in ["y", "yes"]:
                                        print_info(
                                            "🔄 Creating database in the specified page..."
                                        )
                                        # Create database in the page
                                        database = notion.databases.create(
                                            parent={
                                                "type": "page_id",
                                                "page_id": database_id,
                                            },
                                            title=[
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": "Hugo Blog Posts"
                                                    },
                                                }
                                            ],
                                            properties={
                                                "Name": {"title": {}},
                                                "Status": {
                                                    "select": {
                                                        "options": [
                                                            {
                                                                "name": "Draft",
                                                                "color": "gray",
                                                            },
                                                            {
                                                                "name": "Published",
                                                                "color": "green",
                                                            },
                                                        ]
                                                    }
                                                },
                                                "Tags": {"multi_select": {}},
                                                "Category": {
                                                    "select": {
                                                        "options": [
                                                            {
                                                                "name": "Tech",
                                                                "color": "blue",
                                                            },
                                                            {
                                                                "name": "Life",
                                                                "color": "green",
                                                            },
                                                            {
                                                                "name": "Tutorial",
                                                                "color": "orange",
                                                            },
                                                        ]
                                                    }
                                                },
                                                "Created": {"created_time": {}},
                                                "Last edited": {"last_edited_time": {}},
                                            },
                                        )
                                        result = {
                                            "success": True,
                                            "database_id": database["id"],
                                        }
                                        update_progress(
                                            f"Database created in page (ID: {database['id'][:8]}...)"
                                        )
                                        print_success(
                                            "✅ Database successfully created in the specified page!"
                                        )
                                        print_info(
                                            f"📋 New database ID: {database['id']}"
                                        )
                                        print_info(
                                            f"🔗 URL: https://notion.so/{database['id'].replace('-', '')}"
                                        )
                                        database_id = database[
                                            "id"
                                        ]  # Update for next steps

                                        # Create sample post in the new database
                                        print_info(
                                            "📝 Creating sample post in new database..."
                                        )
                                        try:
                                            from src.notion_setup import NotionSetup

                                            setup = NotionSetup(token)
                                            setup.create_sample_post(database["id"])
                                            print_success(
                                                "✅ Sample post created successfully!"
                                            )
                                        except Exception as sample_error:
                                            print_warning(
                                                f"⚠️ Could not create sample post: {str(sample_error)}"
                                            )

                                    else:
                                        sys.exit(1)
                                except Exception as create_error:
                                    print_error(
                                        f"Failed to create database: {str(create_error)}"
                                    )
                                    print_info(
                                        "Please try one of the other options above"
                                    )
                                    sys.exit(1)
                        except Exception as page_error:
                            # Neither database nor page works
                            update_progress("ID validation", False)
                            print_error(f"ID validation failed: {str(db_error)}")
                            print_info(
                                "🔍 This ID is neither a valid Database nor a Page"
                            )
                            print_info("🔧 Troubleshooting steps:")
                            print_info(
                                "   1. Check if the ID is correct and accessible"
                            )
                            print_info(
                                "   2. Make sure the page/database is shared with your integration"
                            )
                            print_info(
                                "   3. Verify the integration has proper permissions"
                            )
                            print_info(
                                "   4. Try copying the ID from the Notion URL again"
                            )
                            print_info("   5. Use --interactive for guided setup")

                            # Show how to find the correct ID
                            print_info("\n📋 How to find the correct Database ID:")
                            print_info("   1. Open your Notion database in the browser")
                            print_info(
                                "   2. Copy the URL: https://notion.so/workspace/ID-HERE"
                            )
                            print_info(
                                "   3. Extract the ID part (32 characters with hyphens)"
                            )
                            print_info(
                                "   4. Make sure the database is shared with your integration"
                            )

                            sys.exit(1)
                except Exception as e:
                    update_progress("ID validation", False)
                    print_error(f"Unexpected error during validation: {str(e)}")
                    print_info("🔧 Try these solutions:")
                    print_info("   1. Check your internet connection")
                    print_info("   2. Verify your Notion token is still valid")
                    print_info("   3. Use --interactive for step-by-step setup")
                    sys.exit(1)
            elif interactive:
                print_info("Starting interactive setup mode...")
                result = run_interactive_setup()
            elif migrate_from:
                print_info(f"Migrating from existing database: {migrate_from}")
                result = run_migrate_database(migrate_from, None, target_folder)
            else:
                print_info("Creating new database with optimized structure...")
                result = run_enhanced_quick_setup(target_folder, skip_sample_posts)

            if result.get("success"):
                database_id = result.get("database_id")
                update_progress(f"Database setup (ID: {database_id[:8]}...)")
            else:
                update_progress("Database setup", False)
                print_error(
                    f"Database setup failed: {result.get('errors', ['Unknown error'])}"
                )
                sys.exit(1)
        except Exception as e:
            update_progress("Database setup", False)
            print_error(f"Database setup failed: {str(e)}")
            sys.exit(1)

        # Step 3: Configure environment and config files
        print_info("⚙️  Step 3/7: Configuring environment and settings...")
        try:
            config_result = setup_configuration(token, database_id, target_folder)
            if config_result.get("success"):
                update_progress("Environment configuration")
            else:
                error_msg = config_result.get("error", "Unknown configuration error")
                print_error(f"Configuration setup failed: {error_msg}")
                print_info("This may cause issues with the sync process")
                update_progress("Environment configuration", False)
                # Don't exit - let the user know but continue
        except Exception as e:
            update_progress("Environment configuration", False)
            print_error(f"Configuration setup failed with exception: {str(e)}")
            print_info("Continuing with setup, but manual configuration may be needed")

        # Step 4: Run initial content sync
        print_info("🔄 Step 4/7: Running initial content sync (Notion → Hugo)...")
        try:
            sync_result = run_notion_pipeline(incremental=False)
            if sync_result.get("success"):
                page_count = len(sync_result.get("page_ids", []))
                update_progress(f"Content sync ({page_count} pages)")
            else:
                update_progress("Content sync", False)
                print_error(
                    "Initial sync failed - this may prevent proper local preview"
                )
        except Exception as e:
            update_progress("Content sync", False)
            print_error(f"Content sync failed: {str(e)}")

        # Step 5: Hugo site build
        print_info("🏗️  Step 5/7: Building Hugo static site...")
        try:
            build_result = run_hugo_pipeline(build=True)
            if build_result.get("build_success"):
                update_progress("Hugo site build")
            else:
                update_progress("Hugo site build", False)
                print_error("Hugo build failed")
        except Exception as e:
            update_progress("Hugo site build", False)
            print_error(f"Hugo build failed: {str(e)}")

        # Step 6: Start local Hugo server
        print_info("🌎 Step 6/7: Starting local Hugo server...")
        hugo_server_started = False
        try:
            # Start Hugo server in the background
            import subprocess
            import time
            import threading

            def start_hugo_server():
                try:
                    subprocess.run(
                        [
                            "hugo",
                            "server",
                            "--bind",
                            "0.0.0.0",
                            "--port",
                            "1313",
                            "--buildDrafts",
                        ],
                        cwd=".",
                        check=False,
                        capture_output=True,
                    )
                except Exception:
                    pass  # Server process will be terminated when setup completes

            # Start server in background thread
            server_thread = threading.Thread(target=start_hugo_server, daemon=True)
            server_thread.start()

            # Give server time to start
            time.sleep(3)

            # Check if server is responding
            try:
                import urllib.request

                urllib.request.urlopen("http://localhost:1313", timeout=2)
                hugo_server_started = True
                update_progress("Hugo server (http://localhost:1313)")
                print_success("✨ Your blog is now running at: http://localhost:1313")
            except Exception:
                print_info(
                    "Hugo server starting... you can access it at http://localhost:1313 in a moment"
                )
                update_progress("Hugo server (starting)")
                hugo_server_started = True

        except Exception as e:
            update_progress("Hugo server", False)
            print_warning(f"Failed to start Hugo server: {str(e)}")
            print_info("You can manually start the server with: hugo server")

        # Step 7: Success confirmation
        print_info("✅ Step 7/7: Validating setup and generating success report...")
        try:
            # Validate that everything is working
            validation_success = True

            # Check if .env exists
            if not os.path.exists(".env"):
                validation_success = False
                print_warning("Missing .env file")

            # Check if config exists
            config_path = "src/config/notion-hugo-config.yaml"
            if not os.path.exists(config_path):
                validation_success = False
                print_warning(f"Missing config file: {config_path}")

            # Check if public directory has content
            public_dir = Path("public")
            if not (public_dir.exists() and any(public_dir.iterdir())):
                validation_success = False
                print_warning("Missing Hugo build output")

            if validation_success:
                update_progress("Setup validation")
            else:
                update_progress("Setup validation", False)

        except Exception as e:
            update_progress("Setup validation", False)
            print_warning(f"Setup validation failed: {str(e)}")

        # Final summary
        print_header("🎉 Core Setup Complete!")

        success_count = len(setup_progress["success_steps"])
        total_steps = setup_progress["total_steps"]

        print_info(
            f"Completed {success_count}/{total_steps} core setup steps successfully"
        )

        if setup_progress["failed_steps"]:
            print_warning("Some steps had issues:")
            for step in setup_progress["failed_steps"]:
                print_info(f"  ⚠️  {step}")

        print_header("🎯 Your Blog is Ready!")
        print_success("✨ Core Notion-Hugo pipeline is working!")

        # Show scenario-specific success message
        if not token:
            print_info("\n🎯 Demo Mode Success!")
            print_info("✅ Sample content generated")
            print_info("✅ Hugo site built successfully")
            print_info("✅ Local server running")
            print_info("\n💡 Next Steps:")
            print_info("1. Explore the sample blog at http://localhost:1313")
            print_info(
                "2. Get your Notion API token from https://www.notion.so/my-integrations"
            )
            print_info(
                "3. Run 'python app.py setup --token YOUR_TOKEN' to connect with Notion"
            )
        elif token and not database_id:
            print_info("\n🚀 New User Success!")
            print_info("✅ Notion database created with optimal structure")
            print_info("✅ Sample posts generated")
            print_info("✅ Configuration files created")
            print_info("✅ Content synced from Notion")
            print_info("✅ Hugo site built successfully")
        elif token and database_id:
            print_info("\n📊 Existing Database Success!")
            print_info("✅ Database validated and optimized")
            print_info("✅ Configuration updated")
            print_info("✅ Content synced from Notion")
            print_info("✅ Hugo site built successfully")

        print_info("\n🔗 What you've accomplished:")
        if token:
            print_info("✅ Notion database created and configured")
            print_info("✅ Sample posts generated (ready to edit!)")
            print_info("✅ Configuration files created (.env, config.yaml)")
            print_info("✅ Content synced from Notion to Hugo markdown")
        print_info("✅ Hugo static site built successfully")
        if hugo_server_started:
            print_info("✅ Local server running at http://localhost:1313")

        # Show important IDs and URLs
        if token and database_id:
            print_info("\n📋 Important Information:")
            print_info(f"🔑 Database ID: {database_id}")
            print_info(
                f"🔗 Database URL: https://notion.so/{database_id.replace('-', '')}"
            )
            config_manager = ConfigManager()
            content_path = Path(config_manager.get_hugo_content_path()) / target_folder
            print_info(f"📁 Content folder: {content_path}/")
            print_info(f"⚙️  Config file: src/config/notion-hugo-config.yaml")
            print_info(f"🔐 Environment file: .env")

        print_info("\n🚀 Next Steps:")
        print_info("1. 🌎 Visit http://localhost:1313 to see your blog")
        if token:
            print_info("2. ✏️ Edit content in your Notion database")
            print_info("3. 🔄 Run 'python app.py sync' to update your blog")
            print_info("4. 🌐 When ready to deploy:")
            print_info("   • python app.py deploy github    # Set up GitHub Pages")
            print_info("   • python app.py deploy vercel    # Set up Vercel")
            print_info("   • python app.py deploy status    # Check deployment status")

        print_info("\n📝 Quick Commands:")
        print_info("   python app.py sync         # Sync from Notion")
        print_info("   python app.py build        # Build Hugo site")
        print_info("   python app.py build --serve # Build and serve locally")

        # Show deployment environment variable info
        if token and database_id:
            print_info("\n🔧 For Deployment (GitHub Pages/Vercel):")
            print_info("Add these environment variables to your deployment platform:")
            print_info(f"   NOTION_TOKEN={token}")
            print_info(f"   NOTION_DATABASE_ID_POSTS={database_id}")
            print_info("   (Optional) HUGO_BASE_URL=https://your-domain.com")

        if hugo_server_started:
            print_success(
                "\n✨ Your blog is live at http://localhost:1313 - go check it out!"
            )
        else:
            print_info("\nℹ️ Start your local server with: hugo server")
            print_success("✨ Your Notion-Hugo blog is ready!")

    except KeyboardInterrupt:
        print_warning("\n🛑 Setup interrupted by user")
        print_info("You can resume setup anytime by running the command again")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n💥 Setup failed with unexpected error: {str(e)}")
        print_info("Please check the error above and try again")
        print_info("For help, visit: https://github.com/your-repo/issues")
        sys.exit(1)


# Add quickstart as an alias for setup
@cli.command()
@click.option(
    "--token",
    required=True,
    help="Notion API token (starts with 'ntn_')",
    prompt="Enter your Notion API token",
)
@click.option(
    "--target-folder",
    default="posts",
    help="Target folder for content (default: posts)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Run interactive setup instead of quick setup",
)
@click.option(
    "--database-id",
    help="Use existing Database ID or Page ID with database blocks (instead of creating new one)",
)
@click.option("--migrate-from", help="Database ID to migrate from (optional)")
@click.option("--skip-sample-posts", is_flag=True, help="Skip sample post generation")
def quickstart(
    token: str,
    target_folder: str,
    interactive: bool,
    database_id: Optional[str],
    migrate_from: Optional[str],
    skip_sample_posts: bool,
) -> None:
    """
    Quick start setup - Get your blog running in minutes.

    This is an alias for the setup command. See 'python app.py setup --help' for details.
    """
    # Call the setup function directly by accessing its callback
    setup.callback(
        token, target_folder, interactive, database_id, migrate_from, skip_sample_posts
    )


def setup_vercel_preview():
    """Setup Vercel for preview deployments"""
    vercel_json = {
        "buildCommand": "python app.py sync && hugo --minify",
        "outputDirectory": "public",
        "framework": None,
        "installCommand": "pip install -r dev/requirements.txt && apt-get update && apt-get install -y hugo",
        "env": {"HUGO_VERSION": "0.128.0"},
    }

    vercel_path = Path("vercel.json")
    if not vercel_path.exists():
        import json

        with open(vercel_path, "w") as f:
            json.dump(vercel_json, f, indent=2)
        print_success("✅ Created vercel.json")
        print_info("  Deploy with: vercel --prod")
    else:
        print_info("  vercel.json already exists")


@cli.command()
@click.option(
    "--incremental/--full",
    default=True,
    help="Use incremental sync (default) or full sync",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without actually doing it",
)
@click.option(
    "--state-file",
    default="src/config/.notion-hugo-state.json",
    help="Path to state file for incremental sync",
)
@click.option(
    "--large-db",
    is_flag=True,
    help="Enable large database mode: limited migration with fallback",
)
@click.option(
    "--professional",
    is_flag=True,
    help="Enable professional migration mode: unlimited processing",
)
def sync(
    incremental: bool,
    dry_run: bool,
    state_file: str,
    large_db: bool,
    professional: bool,
) -> None:
    """
    Sync content from Notion to Hugo markdown files.

    This command fetches your Notion pages and converts them to Hugo-compatible
    markdown files. Use --incremental for faster syncing of only changed content.

    Examples:
        python app.py sync                    # Incremental sync
        python app.py sync --full             # Full sync
        python app.py sync --dry-run          # Preview changes
    """
    if not app.validate_environment():
        sys.exit(1)

    print_header("🔄 Notion Content Sync")

    try:
        # 모드 확인 및 표시
        if professional:
            print_info("🎯 Professional Migration Mode: Unlimited processing enabled")
        elif large_db:
            print_info(
                "📊 Large Database Mode: Limited migration with fallback enabled"
            )
        elif incremental:
            print_info("⚡ Incremental Sync Mode: Changed pages only")
        else:
            print_info("🔄 Full Sync Mode: All pages")

        if dry_run:
            print_info("🧪 Dry Run Mode: No actual changes will be made")

        result = run_notion_pipeline(
            incremental=incremental,
            state_file=state_file,
            dry_run=dry_run,
            large_db_mode=large_db,
            professional_mode=professional,
        )

        if result.get("success"):
            page_count = len(result.get("page_ids", []))
            mode = result.get("mode", "standard")

            if professional:
                pages_processed = result.get("pages_processed", page_count)
                print_success(
                    f"Professional migration completed! {pages_processed} pages processed."
                )
            elif large_db:
                pages_processed = result.get("pages_processed", page_count)
                total_pages = result.get("total_pages", page_count)
                fallback_used = result.get("fallback_used", False)

                if fallback_used:
                    print_warning(
                        f"Large DB mode failed, fallback used. {pages_processed} pages processed."
                    )
                else:
                    print_success(
                        f"Large DB mode completed! {pages_processed}/{total_pages} pages processed."
                    )
            else:
                print_success(
                    f"Sync completed successfully! {page_count} pages processed."
                )

            if dry_run:
                print_info(
                    "This was a dry run - no files were actually created or modified."
                )
        else:
            print_error("Sync failed. Check the error messages above.")
            sys.exit(1)

    except Exception as e:
        print_error(f"Sync failed with error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option(
    "--serve", "-s", is_flag=True, help="Start Hugo development server after build"
)
@click.option("--minify", is_flag=True, help="Minify output files")
@click.option("--hugo-args", help="Additional arguments to pass to Hugo")
def build(serve: bool, minify: bool, hugo_args: Optional[str]) -> None:
    """
    Build the Hugo static site.

    This command processes Hugo content and generates the static site files.
    Use --serve to start a development server for local testing.

    Examples:
        python app.py build                   # Build site
        python app.py build --serve           # Build and serve locally
        python app.py build --minify          # Build with minification
    """
    print_header("Hugo Site Build")

    try:
        hugo_cmd_args = []
        if hugo_args:
            hugo_cmd_args.extend(hugo_args.split())

        if serve:
            hugo_cmd_args.append("server")
            print_info("Building site and starting development server...")
        else:
            print_info("Building static site...")

        if minify and not serve:
            hugo_cmd_args.append("--minify")

        result = run_hugo_pipeline(hugo_args=hugo_cmd_args, build=True)

        if result.get("preprocess_success"):
            print_success("Hugo preprocessing completed")
        else:
            print_error("Hugo preprocessing failed")
            sys.exit(1)

        if not serve and result.get("build_success"):
            print_success("Hugo build completed successfully!")

            # Validate build output
            if validate_hugo_build():
                print_info("Build validation passed")
            else:
                print_error("Build validation failed - empty or corrupted output")
                sys.exit(1)
        elif serve:
            print_info("Development server is now running...")
            print_info("Press Ctrl+C to stop the server")
        else:
            print_error("Hugo build failed")
            sys.exit(1)

    except Exception as e:
        print_error(f"Build failed with error: {str(e)}")
        sys.exit(1)


@cli.group()
def deploy() -> None:
    """
    Deployment commands for various platforms.

    Deploy your Notion-Hugo blog to different hosting platforms.
    Run setup first to ensure your blog is working locally.
    """
    pass


@deploy.command()
@click.option(
    "--sync-first/--no-sync",
    default=True,
    help="Sync from Notion before deploying (default: yes)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deployed without actually doing it",
)
def github(sync_first: bool, dry_run: bool) -> None:
    """
    Deploy to GitHub Pages.

    Sets up GitHub repository, configures GitHub Actions for automatic deployment,
    and deploys your Hugo site to GitHub Pages.

    Examples:
        python app.py deploy github           # Full GitHub deployment
        python app.py deploy github --no-sync # Skip Notion sync
        python app.py deploy github --dry-run # Preview deployment
    """
    print_header("🐙 GitHub Pages Deployment")

    if not app.validate_environment():
        sys.exit(1)

    try:
        # Step 1: Sync from Notion (optional)
        if sync_first:
            print_info("Step 1/3: Syncing from Notion...")
            if not dry_run:
                sync_result = run_notion_pipeline(incremental=False)

                if not sync_result.get("success"):
                    print_error("Notion sync failed - deployment aborted")
                    sys.exit(1)

                print_success("Notion sync completed")
            else:
                print_info("DRY RUN: Skipping Notion sync")
        else:
            print_info("Skipping Notion sync as requested")

        # Step 2: Build Hugo site
        if not dry_run:
            print_info("Step 2/3: Building Hugo site...")
            build_result = run_hugo_pipeline(build=True)

            if not build_result.get("build_success"):
                print_error("Hugo build failed - deployment aborted")
                sys.exit(1)

            # Validate build
            if not validate_hugo_build():
                print_error("Build validation failed - deployment aborted")
                sys.exit(1)

            print_success("Hugo build completed")
        else:
            print_info("DRY RUN: Skipping Hugo build")

        # Step 3: GitHub setup and deployment
        print_info("Step 3/3: Setting up GitHub Pages deployment...")
        if not dry_run:
            # Get token and database ID from environment
            token = os.environ.get("NOTION_TOKEN")
            database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")

            if not token or not database_id:
                print_error(
                    "Missing NOTION_TOKEN or NOTION_DATABASE_ID_POSTS environment variables"
                )
                print_info("Please run setup first or check your .env file")
                sys.exit(1)

            github_result = setup_github_integration(token, database_id)
            if github_result.get("success"):
                print_success(
                    f"GitHub deployment successful: {github_result.get('repo_url', 'N/A')}"
                )
                print_info(
                    "Your blog will be available at your GitHub Pages URL in a few minutes"
                )
            elif github_result.get("manual_setup"):
                print_warning("GitHub setup requires manual completion")
                _print_manual_github_setup_instructions()
            else:
                print_error(
                    f"GitHub deployment failed: {github_result.get('error', 'Unknown error')}"
                )
                sys.exit(1)
        else:
            print_info("DRY RUN: GitHub deployment would be configured")

        print_success("GitHub Pages deployment pipeline completed!")

    except Exception as e:
        print_error(f"GitHub deployment failed with error: {str(e)}")
        sys.exit(1)


@deploy.command()
@click.option(
    "--sync-first/--no-sync",
    default=True,
    help="Sync from Notion before deploying (default: yes)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deployed without actually doing it",
)
def vercel(sync_first: bool, dry_run: bool) -> None:
    """
    Deploy to Vercel.

    Sets up Vercel deployment for your Hugo site with automatic deployments
    from your git repository.

    Examples:
        python app.py deploy vercel           # Full Vercel deployment
        python app.py deploy vercel --no-sync # Skip Notion sync
        python app.py deploy vercel --dry-run # Preview deployment
    """
    print_header("▲ Vercel Deployment")

    if not app.validate_environment():
        sys.exit(1)

    try:
        # Step 1: Sync from Notion (optional)
        if sync_first:
            print_info("Step 1/3: Syncing from Notion...")
            if not dry_run:
                sync_result = run_notion_pipeline(incremental=False)

                if not sync_result.get("success"):
                    print_error("Notion sync failed - deployment aborted")
                    sys.exit(1)

                print_success("Notion sync completed")
            else:
                print_info("DRY RUN: Skipping Notion sync")
        else:
            print_info("Skipping Notion sync as requested")

        # Step 2: Build Hugo site
        if not dry_run:
            print_info("Step 2/3: Building Hugo site...")
            build_result = run_hugo_pipeline(build=True)

            if not build_result.get("build_success"):
                print_error("Hugo build failed - deployment aborted")
                sys.exit(1)

            # Validate build
            if not validate_hugo_build():
                print_error("Build validation failed - deployment aborted")
                sys.exit(1)

            print_success("Hugo build completed")
        else:
            print_info("DRY RUN: Skipping Hugo build")

        # Step 3: Vercel deployment setup
        print_info("Step 3/3: Setting up Vercel deployment...")
        if not dry_run:
            print_info("Vercel deployment setup is coming soon!")
            print_info("For now, please deploy manually:")
            print_info("1. Install Vercel CLI: npm i -g vercel")
            print_info("2. Login: vercel login")
            print_info("3. Deploy: vercel --prod")
        else:
            print_info("DRY RUN: Vercel deployment would be configured")

        print_success("Vercel deployment pipeline completed!")

    except Exception as e:
        print_error(f"Vercel deployment failed with error: {str(e)}")
        sys.exit(1)


@deploy.command()
def status() -> None:
    """
    Check deployment status and configuration.

    Shows the current deployment status, recent deployments,
    and configuration for various hosting platforms.

    Examples:
        python app.py deploy status           # Check all deployment status
    """
    print_header("📋 Deployment Status")

    try:
        # Check if we're in a git repository
        import subprocess

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            repo_url = result.stdout.strip()
            print_info(f"Git repository: {repo_url}")

            # Check if it's a GitHub repository
            if "github.com" in repo_url:
                print_info("🐙 GitHub repository detected")

                # Check if GitHub Actions workflow exists
                workflow_path = Path(".github/workflows")
                if workflow_path.exists():
                    workflows = list(workflow_path.glob("*.yml")) + list(
                        workflow_path.glob("*.yaml")
                    )
                    if workflows:
                        print_success(
                            f"Found {len(workflows)} GitHub Actions workflows"
                        )
                        for workflow in workflows:
                            print_info(f"  - {workflow.name}")
                    else:
                        print_warning("No GitHub Actions workflows found")
                else:
                    print_warning("No .github/workflows directory found")

                # Check GitHub Pages settings (requires gh cli)
                try:
                    subprocess.run(["gh", "--version"], check=True, capture_output=True)
                    # Could add more GitHub-specific checks here
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print_info("GitHub CLI not available for detailed status checks")
            else:
                print_info("Non-GitHub repository")

        except subprocess.CalledProcessError:
            print_warning("Not in a git repository or no remote configured")

        # Check for Vercel configuration
        vercel_config = Path("vercel.json")
        if vercel_config.exists():
            print_info("▲ Vercel configuration found")
        else:
            print_info("▲ No Vercel configuration detected")

        # Check environment variables
        print_info("\nEnvironment Configuration:")
        notion_token = os.environ.get("NOTION_TOKEN")
        if notion_token:
            print_success(
                f"NOTION_TOKEN configured (starts with: {notion_token[:8]}...)"
            )
        else:
            print_warning("NOTION_TOKEN not set")

        database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")
        if database_id:
            print_success(
                f"NOTION_DATABASE_ID_POSTS configured (starts with: {database_id[:8]}...)"
            )
        else:
            print_warning("NOTION_DATABASE_ID_POSTS not set")

        # Check build output
        public_dir = Path("public")
        if public_dir.exists() and any(public_dir.iterdir()):
            file_count = sum(1 for _ in public_dir.rglob("*") if _.is_file())
            print_success(f"Hugo build output ready ({file_count} files)")
        else:
            print_warning(
                "No Hugo build output found - run 'python app.py build' first"
            )

        print_info("\n🚀 Deployment Options:")
        print_info("  python app.py deploy github    # Deploy to GitHub Pages")
        print_info("  python app.py deploy vercel    # Deploy to Vercel")

    except Exception as e:
        print_error(f"Status check failed with error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--fix", is_flag=True, help="Attempt to fix common configuration issues")
@click.option("--github", is_flag=True, help="Validate GitHub Pages specific setup")
def validate(fix: bool, github: bool) -> None:
    """
    Validate your Notion-Hugo setup and identify potential issues.

    This command checks:
    - Environment variables
    - Configuration files
    - Notion API connectivity
    - Database access and permissions
    - Hugo setup
    - Deployment readiness
    """
    print_header("🔍 Notion-Hugo Setup Validation")

    issues = []
    warnings = []
    fixes_applied = []

    # Check environment variables
    print_info("🔐 Checking environment variables...")
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")

    if not notion_token:
        issues.append("NOTION_TOKEN environment variable is not set")
        if fix:
            print_info("💡 To fix: Add NOTION_TOKEN=your_token to your .env file")
    else:
        print_success("✅ NOTION_TOKEN is set")

    if not database_id:
        issues.append("NOTION_DATABASE_ID_POSTS environment variable is not set")
        if fix:
            print_info(
                "💡 To fix: Add NOTION_DATABASE_ID_POSTS=your_db_id to your .env file"
            )
    else:
        print_success(f"✅ NOTION_DATABASE_ID_POSTS is set: {database_id[:8]}...")

    # Check configuration files
    print_info("\n⚙️ Checking configuration files...")
    config_file = Path("notion-hugo.config.yaml")
    env_file = Path(".env")

    if not config_file.exists():
        issues.append("notion-hugo.config.yaml file is missing")
        if fix:
            print_info("💡 To fix: Run 'python app.py setup' to create configuration")
    else:
        print_success("✅ notion-hugo.config.yaml exists")

    if not env_file.exists():
        issues.append(".env file is missing")
        if fix:
            print_info("💡 To fix: Run 'python app.py setup' to create .env file")
    else:
        print_success("✅ .env file exists")

    # Check Notion API connectivity
    print_info("\n🔗 Checking Notion API connectivity...")
    if notion_token:
        try:
            from notion_client import Client

            notion = Client(
                auth=notion_token,
                notion_version="2025-09-03"
            )

            # Test basic API access
            notion.users.list()
            print_success("✅ Notion API connection successful")

            # Test database access if ID is provided
            if database_id:
                try:
                    database = notion.databases.retrieve(database_id=database_id)
                    print_success(
                        f"✅ Database access successful: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}"
                    )

                    # Check database structure
                    properties = database.get("properties", {})
                    required_props = ["Name", "Status", "Tags", "Category"]
                    missing_props = [
                        prop for prop in required_props if prop not in properties
                    ]

                    if missing_props:
                        warnings.append(
                            f"Database missing recommended properties: {', '.join(missing_props)}"
                        )
                        print_warning(
                            f"⚠️ Database missing properties: {', '.join(missing_props)}"
                        )
                    else:
                        print_success("✅ Database has all recommended properties")

                except Exception as e:
                    issues.append(f"Database access failed: {str(e)}")
                    print_error(f"❌ Database access failed: {str(e)}")
                    print_info("💡 Common solutions:")
                    print_info("   • Check if the database ID is correct")
                    print_info(
                        "   • Ensure the database is shared with your integration"
                    )
                    print_info("   • Verify integration permissions")
            else:
                warnings.append(
                    "Cannot test database access without NOTION_DATABASE_ID_POSTS"
                )

        except Exception as e:
            issues.append(f"Notion API connection failed: {str(e)}")
            print_error(f"❌ Notion API connection failed: {str(e)}")
            print_info("💡 Common solutions:")
            print_info("   • Check if your token is valid")
            print_info("   • Verify internet connection")
            print_info("   • Ensure integration has proper permissions")

    # Check Hugo setup
    print_info("\n🏗️ Checking Hugo setup...")
    try:
        import subprocess

        result = subprocess.run(["hugo", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"✅ Hugo is installed: {result.stdout.strip()}")
        else:
            issues.append("Hugo is not installed or not in PATH")
            if fix:
                print_info(
                    "💡 To fix: Install Hugo from https://gohugo.io/installation/"
                )
    except FileNotFoundError:
        issues.append("Hugo is not installed or not in PATH")
        if fix:
            print_info("💡 To fix: Install Hugo from https://gohugo.io/installation/")

    # Check Hugo theme
    config_manager = ConfigManager()
    theme_dir = Path(config_manager.get_theme_path())
    if not theme_dir.exists():
        warnings.append("Hugo theme not found")
        print_warning("⚠️ Hugo theme not found")
        if fix:
            print_info("💡 To fix: Run 'git submodule update --init --recursive'")
    else:
        print_success("✅ Hugo theme found")

    # Check content directory
    content_dir = Path(config_manager.get_hugo_content_path()) / "posts"
    if not content_dir.exists():
        warnings.append("Content directory not found")
        print_warning("⚠️ Content directory not found")
    else:
        print_success("✅ Content directory exists")

    # GitHub Pages specific checks
    if github:
        print_info("\n🐙 Checking GitHub Pages setup...")

        # Check for GitHub repository
        try:
            result = subprocess.run(
                ["git", "remote", "-v"], capture_output=True, text=True
            )
            if "github.com" in result.stdout:
                print_success("✅ GitHub repository detected")
            else:
                warnings.append("GitHub repository not detected")
        except:
            warnings.append("Git repository not found")

        # Check for GitHub Actions workflow
        workflow_dir = Path(".github/workflows")
        if workflow_dir.exists():
            print_success("✅ GitHub Actions workflow directory exists")
        else:
            warnings.append("GitHub Actions workflow not found")
            if fix:
                print_info(
                    "💡 To fix: Run 'python app.py deploy github' to set up GitHub Pages"
                )

    # Summary
    print_header("📊 Validation Summary")

    if not issues and not warnings:
        print_success("🎉 All checks passed! Your setup is ready to go.")
    else:
        if issues:
            print_error(f"❌ Found {len(issues)} issue(s):")
            for i, issue in enumerate(issues, 1):
                print_error(f"   {i}. {issue}")

        if warnings:
            print_warning(f"⚠️ Found {len(warnings)} warning(s):")
            for i, warning in enumerate(warnings, 1):
                print_warning(f"   {i}. {warning}")

        if fixes_applied:
            print_success(f"🔧 Applied {len(fixes_applied)} fix(es):")
            for fix in fixes_applied:
                print_success(f"   • {fix}")

        print_info("\n💡 Next steps:")
        if issues:
            print_info("1. Fix the issues listed above")
            print_info("2. Run 'python app.py validate' again")
        if warnings:
            print_info("3. Consider addressing the warnings for optimal setup")

        print_info("4. Run 'python app.py setup' for guided setup")
        print_info("5. Run 'python app.py sync' to test content sync")


@cli.command()
def status() -> None:
    """
    Show current system status and recent activity.

    Displays information about the last sync, configuration status,
    and deployment readiness.
    """
    print_header("System Status")

    try:
        # Check configuration status
        config = (
            app.config_manager.get_legacy_config()
        )  # Use legacy format for backward compatibility
        deployment_status = app.config_manager.get_deployment_status()

        print_info("Configuration Status:")
        print_info(f"  - Databases configured: {len(config['mount']['databases'])}")
        print_info(f"  - Pages configured: {len(config['mount']['pages'])}")
        print_info(
            f"  - Environment ready: {'Yes' if deployment_status['environment_ready'] else 'No'}"
        )

        # Check for state file
        state_file = Path("src/config/.notion-hugo-state.json")
        if state_file.exists():
            import json

            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    last_sync = state_data.get("last_sync")
                    if last_sync:
                        print_info(f"  - Last sync: {last_sync}")

                    page_count = len(state_data.get("pages", {}))
                    print_info(f"  - Tracked pages: {page_count}")
            except (json.JSONDecodeError, KeyError):
                print_warning("  - State file exists but is corrupted")
        else:
            print_info("  - No previous sync found")

        # Check Hugo build output
        public_dir = Path("public")
        if public_dir.exists() and any(public_dir.iterdir()):
            print_info("  - Hugo build: Available")
            index_file = public_dir / "index.html"
            if index_file.exists():
                file_size = index_file.stat().st_size
                print_info(f"  - Site size: {file_size} bytes")
        else:
            print_info("  - Hugo build: Not found")

        # Overall status
        if deployment_status["ready_to_deploy"]:
            print_success("System is ready for operation!")
        else:
            print_warning("System requires attention")
            for item in deployment_status.get("missing_items", []):
                print_info(f"  ⚠ {item}")

    except Exception as e:
        print_error(f"Status check failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
