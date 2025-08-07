#!/usr/bin/env python3
"""
Script to dynamically create .gitmodules file based on Hugo configuration.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager


def main():
    """Create .gitmodules file with dynamic Hugo root path."""
    try:
        config_manager = ConfigManager()
        config_manager.create_gitmodules_file()
        print("✅ .gitmodules file created successfully")
    except Exception as e:
        print(f"❌ Error creating .gitmodules: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
