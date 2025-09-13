#!/usr/bin/env python3
"""
Entry point for the 5-Stage Notion-Hugo Pipeline CLI.

This allows the application to be run as a module:
    python -m src [command]
    
Commands:
    notion      # Stage 1: Notion Database → notion_markdown/
    process     # Stage 2: notion_markdown/ → hugo_markdown/
    integrate   # Stage 3: hugo_markdown/ → hugo/content/
    build       # Stage 4: hugo/ → hugo/public/
    deploy      # Stage 5: hugo/public/ → hosting
    run         # Run complete pipeline or specific stages
    status      # Show pipeline status

Legacy app.py support is also available for backward compatibility.
"""

import sys
from pathlib import Path

# Try to use the new 5-stage CLI first
try:
    from .cli import cli as new_cli
    
    if __name__ == "__main__":
        # Check if the user wants the old app.py interface
        if len(sys.argv) > 1 and sys.argv[1] in ['setup', 'sync', 'validate']:
            # Fall back to legacy app.py for these commands
            print("ℹ️  Using legacy app.py interface for backward compatibility")
            from .app import cli as legacy_cli
            legacy_cli()
        else:
            # Use the new 5-stage CLI
            new_cli()

except ImportError as e:
    # Fallback to legacy CLI if new one isn't available
    print(f"ℹ️  New CLI not available ({e}), using legacy app.py")
    from .app import cli as legacy_cli
    
    if __name__ == "__main__":
        legacy_cli()