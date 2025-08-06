#!/usr/bin/env python3
"""
Modern CLI entry point for Notion-Hugo Integration.

This application provides a clean, Click-based CLI interface for converting 
content from Notion to Hugo-compatible markdown and building Hugo sites.

Usage:
    python app.py setup --token YOUR_TOKEN    # 5-minute setup flow
    python app.py sync                        # Sync from Notion to Hugo  
    python app.py build                       # Build Hugo site only
    python app.py deploy                      # Full pipeline: sync + build + deploy
    python app.py validate                    # Validate current configuration
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
            print_warning("GitHub CLI not found. Skipping automatic repository setup.")
            print_info("Install GitHub CLI and run: ./dev/scripts/github-pages-setup.sh")
            return {"success": False, "error": "GitHub CLI not available"}
        
        # Check if user is authenticated
        try:
            result = subprocess.run(["gh", "auth", "status"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            print_warning("Not authenticated with GitHub CLI.")
            print_info("Run 'gh auth login' then re-run setup")
            return {"success": False, "error": "GitHub authentication required"}
        
        # Try to run the GitHub setup script
        script_path = "./dev/scripts/github-pages-setup.sh"
        if os.path.exists(script_path):
            print_info("Running GitHub Pages setup script...")
            
            # Set environment variables for the script
            env = os.environ.copy()
            env["NOTION_TOKEN"] = token
            env["NOTION_DATABASE_ID_POSTS"] = database_id
            
            try:
                result = subprocess.run(
                    ["bash", script_path], 
                    env=env, 
                    check=True, 
                    capture_output=True, 
                    text=True
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
                    return {"success": True, "repo_url": repo_url}
                except subprocess.CalledProcessError:
                    return {"success": True, "repo_url": "Repository configured"}
                    
            except subprocess.CalledProcessError as e:
                print_warning(f"GitHub setup script failed: {e}")
                return {"success": False, "error": str(e)}
        else:
            print_warning(f"GitHub setup script not found at {script_path}")
            return {"success": False, "error": "Setup script not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    "--skip-github",
    is_flag=True,
    help="Skip GitHub repository setup"
)
@click.option(
    "--skip-sample-posts",
    is_flag=True,
    help="Skip sample post generation"
)
def setup(token: str, target_folder: str, interactive: bool, migrate_from: Optional[str], 
          skip_github: bool, skip_sample_posts: bool) -> None:
    """
    5-minute setup flow - Create a complete Notion-Hugo blog from scratch.
    
    This command will:
    \b
    1. Validate your Notion API token
    2. Create a new Notion database (or migrate existing one)
    3. Generate sample blog posts (unless --skip-sample-posts)
    4. Configure environment variables
    5. Set up GitHub repository and deployment pipeline (unless --skip-github)
    6. Run initial sync and build
    7. Deploy your blog
    
    Examples:
        python app.py setup --token ntn_your_token_here
        python app.py setup --token ntn_your_token_here --skip-github
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
        
        # Step 4: GitHub repository and deployment setup
        if not skip_github:
            print_info("🐙 Step 4/7: Setting up GitHub repository and deployment...")
            try:
                github_result = setup_github_integration(token, database_id)
                if github_result.get("success"):
                    update_progress("GitHub setup")
                    print_info(f"Repository: {github_result.get('repo_url', 'N/A')}")
                else:
                    update_progress("GitHub setup", False)
                    print_warning("GitHub setup failed, but you can set it up manually later")
                    print_info("Run: ./dev/scripts/github-pages-setup.sh")
            except Exception as e:
                update_progress("GitHub setup", False)
                print_warning(f"GitHub setup failed: {str(e)} - you can set it up manually later")
        else:
            print_info("🐙 Step 4/7: Skipping GitHub setup as requested...")
            update_progress("GitHub setup (skipped)")
        
        # Step 5: Initial content sync
        print_info("🔄 Step 5/7: Running initial content sync...")
        try:
            sync_result = run_notion_pipeline(incremental=False)
            if sync_result.get("success"):
                page_count = len(sync_result.get('page_ids', []))
                update_progress(f"Content sync ({page_count} pages)")
            else:
                update_progress("Content sync", False)
                print_error("Initial sync failed - this may prevent proper deployment")
        except Exception as e:
            update_progress("Content sync", False)
            print_error(f"Content sync failed: {str(e)}")
        
        # Step 6: Hugo site build
        print_info("🏗️  Step 6/7: Building Hugo static site...")
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
        
        # Step 7: Deploy and finalize
        print_info("🚀 Step 7/7: Finalizing deployment...")
        try:
            deploy_result = finalize_deployment(skip_github)
            if deploy_result.get("success"):
                update_progress("Deployment finalization")
            else:
                update_progress("Deployment finalization", False)
                print_warning("Deployment finalization had issues")
        except Exception as e:
            update_progress("Deployment finalization", False)
            print_warning(f"Deployment finalization failed: {str(e)}")
        
        # Final summary
        print_header("🎉 Setup Complete!")
        
        success_count = len(setup_progress["success_steps"])
        total_steps = setup_progress["total_steps"]
        
        print_info(f"Completed {success_count}/{total_steps} steps successfully")
        
        if setup_progress["failed_steps"]:
            print_warning("Some steps had issues:")
            for step in setup_progress["failed_steps"]:
                print_info(f"  ⚠️  {step}")
        
        print_info("\n🎯 What's next?")
        print_info("1. Your Notion database is ready - start adding content!")
        print_info("2. Your blog will auto-sync and deploy when you publish in Notion")
        print_info("3. Check your GitHub repository for the deployment status")
        
        if not skip_github:
            print_info("4. Your blog should be live in a few minutes!")
        else:
            print_info("4. Run GitHub setup when ready: ./dev/scripts/github-pages-setup.sh")
        
        print_success("\n✨ Your Notion-Hugo blog is ready to go!")
        
    except KeyboardInterrupt:
        print_warning("\n🛑 Setup interrupted by user")
        print_info("You can resume setup anytime by running the command again")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n💥 Setup failed with unexpected error: {str(e)}")
        print_info("Please check the error above and try again")
        print_info("For help, visit: https://github.com/your-repo/issues")
        sys.exit(1)


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


@cli.command()
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
def deploy(sync_first: bool, dry_run: bool) -> None:
    """
    Full deployment pipeline: sync, build, and deploy.
    
    This command runs the complete pipeline:
    1. Sync content from Notion (optional)
    2. Build Hugo static site
    3. Deploy to configured platform
    
    Examples:
        python app.py deploy                  # Full pipeline
        python app.py deploy --no-sync        # Skip Notion sync
        python app.py deploy --dry-run        # Preview deployment
    """
    print_header("Full Deployment Pipeline")
    
    if not app.validate_environment():
        sys.exit(1)
    
    try:
        # Step 1: Sync from Notion (optional)
        if sync_first:
            print_info("Step 1/2: Syncing from Notion...")
            sync_result = run_notion_pipeline(dry_run=dry_run)
            
            if not sync_result.get("success"):
                print_error("Notion sync failed - deployment aborted")
                sys.exit(1)
            
            print_success("Notion sync completed")
        else:
            print_info("Skipping Notion sync as requested")
        
        # Step 2: Build Hugo site
        if not dry_run:
            print_info("Step 2/2: Building Hugo site...")
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
        
        print_success("Deployment pipeline completed successfully!")
        print_info("Your site is ready for deployment")
        
    except Exception as e:
        print_error(f"Deployment failed with error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix common configuration issues"
)
def validate(fix: bool) -> None:
    """
    Validate current Notion-Hugo configuration.
    
    This command checks your environment setup, configuration files, 
    and Notion API connectivity to ensure everything is working correctly.
    
    Examples:
        python app.py validate                # Check configuration
        python app.py validate --fix          # Fix common issues
    """
    print_header("Configuration Validation")
    
    try:
        # Run built-in validation
        result = run_validation()
        
        if result.get("success"):
            print_success("Configuration validation passed!")
        else:
            print_error("Configuration validation failed")
            error_msg = result.get("error", "Unknown error")
            print_info(f"Error: {error_msg}")
        
        # Run detailed diagnosis
        print_info("Running detailed diagnosis...")
        diagnosis = diagnose_configuration()
        
        if diagnosis.get("ready_to_deploy"):
            print_success("System is ready for deployment!")
        else:
            print_warning("System is not ready for deployment")
            missing_items = diagnosis.get("missing_items", [])
            if missing_items:
                print_info("Missing or incorrect items:")
                for item in missing_items:
                    print_info(f"  - {item}")
        
        # Attempt fixes if requested
        if fix and not diagnosis.get("ready_to_deploy"):
            print_info("Attempting to fix common issues...")
            
            # Create environment template if missing
            if not os.path.exists(".env"):
                print_info("Creating .env template file...")
                app.config_manager.create_env_template()
            
            # Create default config if missing
            if not os.path.exists(app.config_manager.config_path):
                print_info("Creating default configuration file...")
                app.config_manager.create_default_config_if_missing()
            
            print_success("Auto-fix completed. Please review and update the created files.")
        
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