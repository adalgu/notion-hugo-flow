#!/usr/bin/env python3
"""
Notion-Hugo Flow - Main Entry Point

This is the primary entry point for the Notion-Hugo Flow blog system.
It provides a modern CLI interface with comprehensive setup capabilities.

Quick Start:
    python app.py setup --token YOUR_NOTION_TOKEN

Commands:
    setup     - 5-minute complete blog setup (from token to live blog)
    sync      - Sync content from Notion to Hugo markdown
    build     - Build Hugo static site
    deploy    - Full deployment pipeline (sync + build + deploy)
    validate  - Validate current configuration
    status    - Show system status

Examples:
    # Complete setup from scratch
    python app.py setup --token ntn_your_token_here
    
    # Setup without GitHub (manual deployment)
    python app.py setup --token ntn_your_token_here --skip-github
    
    # Interactive setup with choices
    python app.py setup --token ntn_your_token_here --interactive
    
    # Just sync content from Notion
    python app.py sync
    
    # Build Hugo site
    python app.py build --serve
    
    # Full deployment pipeline
    python app.py deploy
    
    # Check current status
    python app.py status
"""

import os
import sys
from pathlib import Path

# Ensure we can import from src/
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Handle missing dependencies gracefully
try:
    # Import the modern CLI
    from src.app import cli, print_error, print_info
    
    if __name__ == "__main__":
        try:
            cli()
        except KeyboardInterrupt:
            print_info("\n🛑 Operation cancelled by user")
            sys.exit(130)
        except ImportError as e:
            print_error(f"Missing dependencies: {str(e)}")
            print_info("Install dependencies with: pip install -r dev/requirements.txt")
            sys.exit(1)
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            print_info("For help, run: python app.py --help")
            sys.exit(1)

except ImportError as e:
    # Fallback error handling when src imports fail
    print(f"❌ Failed to import Notion-Hugo Flow CLI: {str(e)}")
    print("📦 Install dependencies first:")
    print("   pip install notion-client python-dotenv pyyaml click")
    print("   # or")
    print("   pip install -r dev/requirements.txt")
    print()
    print("📚 For setup help, see: dev/docs/SETUP_GUIDE.md")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    sys.exit(1)