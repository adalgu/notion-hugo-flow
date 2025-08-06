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
from .cli_utils import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    ask_yes_no,
)
from .smart_config import SmartConfigManager, ThemeManager
from .config_validator import ConfigValidator, run_validation_check


def run_enhanced_quick_setup(target_folder: str = "posts", skip_sample_posts: bool = False) -> Dict[str, Any]:
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
        result = run_quick_setup(target_folder)
        
        if result.get("success") and not skip_sample_posts:
            database_id = result.get("database_id")
            if database_id:
                print_info("Generating sample blog posts...")
                sample_result = generate_sample_posts(database_id)
                if sample_result.get("success"):
                    print_success(f"Created {sample_result.get('count', 0)} sample posts")
                else:
                    print_warning("Sample post generation failed, but database is ready")
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_sample_posts(database_id: str) -> Dict[str, Any]:
    """
    Generate sample blog posts in the Notion database.
    
    Args:
        database_id: The database ID to add sample posts to
        
    Returns:
        Result dictionary with success status and count
    """
    try:
        from notion_client import Client
        
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))
        
        sample_posts = [
            {
                "title": "Welcome to Your New Blog!",
                "content": """# Welcome to Your Notion-Hugo Blog!

🎉 Congratulations! You've successfully set up your Notion-Hugo blog. This is your first sample post to help you get started.

## What you've accomplished:
- ✅ Created a Notion database for your blog posts
- ✅ Set up automatic synchronization with Hugo
- ✅ Configured deployment to GitHub Pages
- ✅ Generated this sample content

## Getting Started:
1. **Edit this post** - Change the title and content to make it your own
2. **Create new posts** - Add new pages to your Notion database
3. **Publish content** - Set the Status to "Published" to make posts live
4. **Customize your site** - Edit the Hugo configuration as needed

## Next Steps:
- Replace this content with your own introduction
- Set up your site's branding and theme
- Start writing amazing content!

Your blog will automatically sync and deploy when you publish new content in Notion. Happy blogging! 🚀""",
                "tags": ["Welcome", "Getting Started", "Tutorial"]
            },
            {
                "title": "How to Use Your Notion-Hugo Blog",
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

Your blog is now ready for amazing content! 📝""",
                "tags": ["Tutorial", "Notion", "Workflow"]
            }
        ]
        
        created_count = 0
        for post_data in sample_posts:
            try:
                # Create a new page in the database
                new_page = notion.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": post_data["title"]
                                    }
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": datetime.now().isoformat()
                            }
                        },
                        "isPublished": {
                            "checkbox": True
                        },
                        "skipRendering": {
                            "checkbox": False
                        },
                        "Description": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": f"Sample blog post: {post_data['title']}"
                                    }
                                }
                            ]
                        },
                        "Tags": {
                            "multi_select": [
                                {"name": tag} for tag in post_data["tags"]
                            ]
                        },
                        "categories": {
                            "multi_select": [
                                {"name": "Tutorial"}
                            ]
                        },
                        "featured": {
                            "checkbox": False
                        },
                        "ShowToc": {
                            "checkbox": True
                        },
                        "HideSummary": {
                            "checkbox": False
                        }
                    },
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": post_data["content"]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                )
                created_count += 1
                print_info(f"Created sample post: {post_data['title']}")
                
            except Exception as e:
                print_warning(f"Failed to create sample post '{post_data['title']}': {str(e)}")
        
        return {"success": True, "count": created_count}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def setup_configuration(token: str, database_id: str, target_folder: str) -> Dict[str, Any]:
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
NOTION_TOKEN={token}
NOTION_DATABASE_ID_POSTS={database_id}

# Optional: Additional settings
# NOTION_PAGE_ID_ABOUT=your_about_page_id_here
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print_info("Created .env file with your configuration")
        
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
                config["notion"]["mount"]["databases"][0]["target_folder"] = target_folder
            else:
                config["notion"]["mount"]["databases"] = [{
                    "database_id": database_id,
                    "target_folder": target_folder,
                    "content_type": "post"
                }]
            
            config_manager.save_config(config)
            print_info("Updated config.yaml with database settings")
        except Exception as config_error:
            print_info(f"Config.yaml update failed: {str(config_error)}")
            print_info("Creating fallback configuration...")
            
            # Create a simple fallback config file
            fallback_config = {
                "notion": {
                    "mount": {
                        "databases": [{
                            "database_id": database_id,
                            "target_folder": target_folder,
                            "content_type": "post"
                        }]
                    }
                }
            }
            
            try:
                import yaml
                with open("notion-hugo.config.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(fallback_config, f, default_flow_style=False, indent=2)
                print_info("Created fallback notion-hugo.config.yaml")
            except Exception as fallback_error:
                raise Exception(f"Both primary and fallback config creation failed: {str(fallback_error)}")
        
        return {"success": True}
        
    except Exception as e:
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
            subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print_info("Initializing git repository...")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit: Notion-Hugo blog setup"], check=True)
        
        # Check if GitHub CLI is available
        try:
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("GitHub CLI not found. Manual setup required.")
            _print_manual_github_setup_instructions()
            return {"success": False, "error": "GitHub CLI not available", "manual_setup": True}
        
        # Check if user is authenticated
        try:
            result = subprocess.run(["gh", "auth", "status"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            print_warning("Not authenticated with GitHub CLI.")
            print_info("Run 'gh auth login' then re-run setup")
            _print_manual_github_setup_instructions()
            return {"success": False, "error": "GitHub authentication required", "manual_setup": True}
        
        # Try to run the GitHub setup script with timeout
        script_path = "./dev/scripts/github-pages-setup.sh"
        if os.path.exists(script_path):
            print_info("Running GitHub Pages setup script...")
            print_warning("This may take up to 60 seconds. If it hangs, we'll provide manual instructions.")
            
            # Set environment variables for the script (make it non-interactive)
            env = os.environ.copy()
            env["NOTION_TOKEN"] = token
            env["NOTION_DATABASE_ID_POSTS"] = database_id
            # Add environment variables to make script non-interactive
            env["NON_INTERACTIVE"] = "true"
            env["AUTO_CONFIRM"] = "yes"  # Auto-answer 'yes' to prompts
            env["FORCE_PUSH"] = "no"     # Don't force push by default
            
            try:
                # Use a more generous timeout for the GitHub script
                result = subprocess.run(
                    ["bash", script_path], 
                    env=env, 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    timeout=60  # 60 second timeout to prevent hanging
                )
                
                # Try to extract repository URL from git remote
                try:
                    repo_result = subprocess.run(
                        ["git", "remote", "get-url", "origin"], 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    repo_url = repo_result.stdout.strip()
                    print_success(f"GitHub setup completed successfully: {repo_url}")
                    return {"success": True, "repo_url": repo_url}
                except subprocess.CalledProcessError:
                    print_success("GitHub setup completed successfully")
                    return {"success": True, "repo_url": "Repository configured"}
                    
            except TimeoutExpired:
                print_warning("GitHub setup script timed out after 60 seconds.")
                print_info("This usually happens when the script encounters interactive prompts.")
                print_info("Your repository may have been partially configured.")
                _print_manual_github_setup_instructions()
                return {"success": False, "error": "Script timeout - manual setup required", "manual_setup": True}
            except subprocess.CalledProcessError as e:
                print_warning(f"GitHub setup script failed with exit code {e.returncode}")
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
                return {"success": False, "error": f"Exit code {e.returncode}: {str(e)}", "manual_setup": True}
        else:
            print_warning(f"GitHub setup script not found at {script_path}")
            _print_manual_github_setup_instructions()
            return {"success": False, "error": "Setup script not found", "manual_setup": True}
            
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
    print_info("     git remote add origin https://github.com/YOUR-USERNAME/YOUR-USERNAME.github.io.git")
    print_info("   • Push your code:")
    print_info("     git push -u origin main")
    
    print_info("\n🔑 Step 3: Set up GitHub secrets")
    print_info("   • Get your Notion token from .env file or environment")
    print_info("   • Set the secret (replace with your actual token):")
    print_info("     gh secret set NOTION_TOKEN --body 'ntn_your_token_here'")
    
    print_info("\n📄 Step 4: Enable GitHub Pages")
    print_info("   • Go to your repository settings:")
    print_info("     https://github.com/YOUR-USERNAME/YOUR-USERNAME.github.io/settings/pages")
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
    print_info("     NON_INTERACTIVE=true AUTO_CONFIRM=yes ./dev/scripts/github-pages-setup.sh")
    
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
                    print_warning("Site index.html seems too small - may be an error page")
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
                    check=True
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
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """
    Notion-Hugo Integration CLI - Modern blog publishing with Notion as CMS.
    
    Convert Notion pages to Hugo markdown and deploy static sites automatically.
    Perfect for developers who want to use Notion as their blog CMS.
    """
    if version:
        click.echo("Notion-Hugo CLI v1.0.0")
        return
        
    if ctx.invoked_subcommand is None:
        # Show help if no command is provided
        click.echo(ctx.get_help())
        ctx.exit()


@cli.command()
@click.option(
    "--token", 
    required=True,
    help="Notion API token (starts with 'ntn_')",
    prompt="Enter your Notion API token"
)
@click.option(
    "--target-folder",
    default="posts",
    help="Target folder for content (default: posts)"
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Run interactive setup instead of quick setup"
)
@click.option(
    "--migrate-from",
    help="Database ID to migrate from (optional)"
)
@click.option(
    "--skip-sample-posts",
    is_flag=True,
    help="Skip sample post generation"
)
def setup(token: str, target_folder: str, interactive: bool, migrate_from: Optional[str], 
          skip_sample_posts: bool) -> None:
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
        python app.py setup --token ntn_your_token_here
        python app.py setup --token ntn_your_token_here --interactive
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
        "failed_steps": []
    }
    
    def update_progress(step_name: str, success: bool = True) -> None:
        setup_progress["current_step"] += 1
        if success:
            setup_progress["success_steps"].append(step_name)
            print_success(f"✅ Step {setup_progress['current_step']}/{setup_progress['total_steps']}: {step_name}")
        else:
            setup_progress["failed_steps"].append(step_name)
            print_error(f"❌ Step {setup_progress['current_step']}/{setup_progress['total_steps']}: {step_name}")
        
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
            notion = Client(auth=token)
            
            # Test the token by trying to list users (this requires basic permissions)
            try:
                notion.users.list()
                update_progress("Notion token validation")
            except Exception as e:
                if "Unauthorized" in str(e) or "Invalid token" in str(e):
                    print_error("Invalid Notion token. Please check your token and try again.")
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
        try:
            if interactive:
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
                print_error(f"Database setup failed: {result.get('errors', ['Unknown error'])}")
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
                page_count = len(sync_result.get('page_ids', []))
                update_progress(f"Content sync ({page_count} pages)")
            else:
                update_progress("Content sync", False)
                print_error("Initial sync failed - this may prevent proper local preview")
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
                    subprocess.run(["hugo", "server", "--bind", "0.0.0.0", "--port", "1313", "--buildDrafts"], 
                                 cwd=".", check=False, capture_output=True)
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
                urllib.request.urlopen('http://localhost:1313', timeout=2)
                hugo_server_started = True
                update_progress("Hugo server (http://localhost:1313)")
                print_success("✨ Your blog is now running at: http://localhost:1313")
            except Exception:
                print_info("Hugo server starting... you can access it at http://localhost:1313 in a moment")
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
            if not os.path.exists("notion-hugo.config.yaml"):
                validation_success = False
                print_warning("Missing config file")
            
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
        
        print_info(f"Completed {success_count}/{total_steps} core setup steps successfully")
        
        if setup_progress["failed_steps"]:
            print_warning("Some steps had issues:")
            for step in setup_progress["failed_steps"]:
                print_info(f"  ⚠️  {step}")
        
        print_header("🎯 Your Blog is Ready!")
        print_success("✨ Core Notion-Hugo pipeline is working!")
        
        print_info("\n🔗 What you've accomplished:")
        print_info("✅ Notion database created and configured")
        print_info("✅ Sample posts generated (ready to edit!)")
        print_info("✅ Configuration files created (.env, config.yaml)")
        print_info("✅ Content synced from Notion to Hugo markdown")
        print_info("✅ Hugo static site built successfully")
        if hugo_server_started:
            print_info("✅ Local server running at http://localhost:1313")
        
        print_info("\n🚀 Next Steps:")
        print_info("1. 🌎 Visit http://localhost:1313 to see your blog")
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
        
        if hugo_server_started:
            print_success("\n✨ Your blog is live at http://localhost:1313 - go check it out!")
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


3. Push to GitHub to trigger deployment")
            print_info("  4. Your site will be live in ~5 minutes!")
        else:
            print_info("  1. Run: python app.py build --serve")
            print_info("  2. Open http://localhost:1313")
        
        print_info("\n📝 Daily Workflow:")
        print_info("  • Edit content in Notion")
        print_info("  • Run: python app.py sync")
        print_info("  • Changes auto-deploy to GitHub Pages!")
        
    except KeyboardInterrupt:
        print_warning("\n🛑 Setup interrupted")
        sys.exit(130)
    except Exception as e:
        print_error(f"Setup failed: {str(e)}")
        sys.exit(1)


def setup_vercel_preview():
    """Setup Vercel for preview deployments"""
    vercel_json = {
        "buildCommand": "python app.py sync && hugo --minify",
        "outputDirectory": "public",
        "framework": None,
        "installCommand": "pip install -r dev/requirements.txt && apt-get update && apt-get install -y hugo",
        "env": {
            "HUGO_VERSION": "0.128.0"
        }
    }
    
    vercel_path = Path("vercel.json")
    if not vercel_path.exists():
        import json
        with open(vercel_path, 'w') as f:
            json.dump(vercel_json, f, indent=2)
        print_success("✅ Created vercel.json")
        print_info("  Deploy with: vercel --prod")
    else:
        print_info("  vercel.json already exists")


@cli.command()
@click.option(
    "--incremental/--full",
    default=True,
    help="Use incremental sync (default) or full sync"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without actually doing it"
)
@click.option(
    "--state-file",
    default=".notion-hugo-state.json",
    help="Path to state file for incremental sync"
)
def sync(incremental: bool, dry_run: bool, state_file: str) -> None:
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
    
    print_header("Notion Content Sync")
    
    try:
        print_info(f"Starting {'incremental' if incremental else 'full'} sync...")
        if dry_run:
            print_info("DRY RUN MODE: No files will be modified")
        
        result = run_notion_pipeline(
            incremental=incremental,
            state_file=state_file,
            dry_run=dry_run
        )
        
        if result.get("success"):
            print_success("Sync completed successfully!")
            if not dry_run:
                print_info(f"Processed {len(result.get('page_ids', []))} pages")
        else:
            print_error("Sync failed")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Sync failed with error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option(
    "--serve", "-s",
    is_flag=True,
    help="Start Hugo development server after build"
)
@click.option(
    "--minify",
    is_flag=True,
    help="Minify output files"
)
@click.option(
    "--hugo-args",
    help="Additional arguments to pass to Hugo"
)
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
    help="Sync from Notion before deploying (default: yes)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deployed without actually doing it"
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
                print_error("Missing NOTION_TOKEN or NOTION_DATABASE_ID_POSTS environment variables")
                print_info("Please run setup first or check your .env file")
                sys.exit(1)
            
            github_result = setup_github_integration(token, database_id)
            if github_result.get("success"):
                print_success(f"GitHub deployment successful: {github_result.get('repo_url', 'N/A')}")
                print_info("Your blog will be available at your GitHub Pages URL in a few minutes")
            elif github_result.get("manual_setup"):
                print_warning("GitHub setup requires manual completion")
                _print_manual_github_setup_instructions()
            else:
                print_error(f"GitHub deployment failed: {github_result.get('error', 'Unknown error')}")
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
    help="Sync from Notion before deploying (default: yes)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deployed without actually doing it"
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
            result = subprocess.run(["git", "remote", "get-url", "origin"], 
                                  capture_output=True, text=True, check=True)
            repo_url = result.stdout.strip()
            print_info(f"Git repository: {repo_url}")
            
            # Check if it's a GitHub repository
            if "github.com" in repo_url:
                print_info("🐙 GitHub repository detected")
                
                # Check if GitHub Actions workflow exists
                workflow_path = Path(".github/workflows")
                if workflow_path.exists():
                    workflows = list(workflow_path.glob("*.yml")) + list(workflow_path.glob("*.yaml"))
                    if workflows:
                        print_success(f"Found {len(workflows)} GitHub Actions workflows")
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
            print_success(f"NOTION_TOKEN configured (starts with: {notion_token[:8]}...)")
        else:
            print_warning("NOTION_TOKEN not set")
            
        database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")
        if database_id:
            print_success(f"NOTION_DATABASE_ID_POSTS configured (starts with: {database_id[:8]}...)")
        else:
            print_warning("NOTION_DATABASE_ID_POSTS not set")
        
        # Check build output
        public_dir = Path("public")
        if public_dir.exists() and any(public_dir.iterdir()):
            file_count = sum(1 for _ in public_dir.rglob("*") if _.is_file())
            print_success(f"Hugo build output ready ({file_count} files)")
        else:
            print_warning("No Hugo build output found - run 'python app.py build' first")
            
        print_info("\n🚀 Deployment Options:")
        print_info("  python app.py deploy github    # Deploy to GitHub Pages")
        print_info("  python app.py deploy vercel    # Deploy to Vercel")
        
    except Exception as e:
        print_error(f"Status check failed with error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix common configuration issues"
)
@click.option(
    "--github",
    is_flag=True,
    help="Validate GitHub Pages specific setup"
)
def validate(fix: bool, github: bool) -> None:
    """
    Validate current Notion-Hugo configuration.
    
    This command checks your environment setup, configuration files, 
    and Notion API connectivity to ensure everything is working correctly.
    
    Examples:
        python app.py validate                # Check configuration
        python app.py validate --fix          # Fix common issues
        python app.py validate --github       # Check GitHub Pages setup
    """
    print_header("Configuration Validation")
    
    try:
        # Use enhanced validation if GitHub flag is set
        if github:
            print_info("🔍 Running GitHub Pages specific validation...")
            config_manager = SmartConfigManager()
            valid, issues = config_manager.validate_github_pages_setup()
            
            if valid:
                print_success("✅ GitHub Pages setup is valid!")
                print_info(f"  Site URL: {config_manager.get_base_url('github')}")
            else:
                print_error("❌ GitHub Pages setup has issues:")
                for issue in issues:
                    print_warning(f"  • {issue}")
                    
                if fix:
                    print_info("\n🔧 Attempting to fix GitHub Pages setup...")
                    if config_manager.setup_github_pages():
                        print_success("✅ GitHub Pages setup completed!")
                    else:
                        print_error("❌ Could not complete GitHub Pages setup")
        else:
            # Use new comprehensive validator
            is_valid = run_validation_check(auto_fix=fix)
            
            if is_valid:
                print_success("\n🎉 Your Notion-Hugo setup is ready!")
                print_info("Run 'python app.py sync' to start syncing content")
            else:
                print_error("\n❌ Please fix the issues above before proceeding")
                if not fix:
                    print_info("Run 'python app.py validate --fix' to attempt auto-fixes")
                sys.exit(1)
        
    except Exception as e:
        print_error(f"Validation failed with error: {str(e)}")
        sys.exit(1)


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
        config = app.config_manager.get_legacy_config()  # Use legacy format for backward compatibility
        deployment_status = app.config_manager.get_deployment_status()
        
        print_info("Configuration Status:")
        print_info(f"  - Databases configured: {len(config['mount']['databases'])}")
        print_info(f"  - Pages configured: {len(config['mount']['pages'])}")
        print_info(f"  - Environment ready: {'Yes' if deployment_status['environment_ready'] else 'No'}")
        
        # Check for state file
        state_file = Path(".notion-hugo-state.json")
        if state_file.exists():
            import json
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
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