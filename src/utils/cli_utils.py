"""
CLI utilities for improved user experience with Notion IDs and database management.
"""

import os
import re
from typing import Optional
from pathlib import Path


def print_success(message: str) -> None:
    """Print a success message with green color."""
    print(f"✅ {message}")


def print_error(message: str) -> None:
    """Print an error message with red color."""
    print(f"❌ {message}")


def print_warning(message: str) -> None:
    """Print a warning message with yellow color."""
    print(f"⚠️ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"ℹ️ {message}")


def print_header(title: str, width: int = 60) -> None:
    """
    Print an emphasized header.
    
    Args:
        title: The title to display
        width: Total width of the header
    """
    print("\n" + "=" * width)
    padding = (width - len(title)) // 2
    print(" " * padding + title)
    print("=" * width + "\n")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """
    Ask a yes/no question and get the response.
    
    Args:
        question: The question to ask
        default: Default value (True: yes, False: no)
        
    Returns:
        User's choice (True: yes, False: no)
    """
    default_text = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {default_text}: ").strip().lower()
        
        if not response:
            return default
        
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
            
        print_warning("Please respond with 'y' or 'n'.")


def extract_notion_id_from_url(url: str) -> Optional[str]:
    """
    Extract Notion ID from a URL with improved error handling and validation.

    Args:
        url: Notion URL (e.g., https://notion.so/workspace/8a021de7-2bda-434d-b255-d7cc94ebb567)

    Returns:
        Extracted ID or None if invalid
    """
    if not url or not isinstance(url, str):
        return None

    # Remove whitespace and common prefixes
    url = url.strip()

    # Handle different URL formats
    patterns = [
        # Standard Notion URL
        r"https?://(?:www\.)?notion\.so/[^/]+/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
        # URL with query parameters
        r"https?://(?:www\.)?notion\.so/[^/]+/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\?",
        # URL with hash
        r"https?://(?:www\.)?notion\.so/[^/]+/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})#",
        # Direct ID (already extracted)
        r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$",
        # ID without hyphens
        r"^([a-f0-9]{32})$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            id_str = match.group(1)

            # If it's a 32-character string without hyphens, add hyphens
            if len(id_str) == 32 and "-" not in id_str:
                id_str = f"{id_str[:8]}-{id_str[8:12]}-{id_str[12:16]}-{id_str[16:20]}-{id_str[20:]}"

            # Validate the ID format
            if is_valid_notion_id(id_str):
                return id_str

    return None


def is_valid_notion_id(id_str: str) -> bool:
    """
    Validate if a string is a valid Notion ID format.

    Args:
        id_str: String to validate

    Returns:
        True if valid Notion ID format
    """
    if not id_str or not isinstance(id_str, str):
        return False

    # Remove any whitespace
    id_str = id_str.strip()

    # Check UUID format with hyphens
    uuid_pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"

    return bool(re.match(uuid_pattern, id_str, re.IGNORECASE))


def format_notion_id(id_str: str) -> str:
    """
    Format a Notion ID for display with truncation and validation.

    Args:
        id_str: Notion ID to format

    Returns:
        Formatted ID string
    """
    if not is_valid_notion_id(id_str):
        return f"Invalid ID: {id_str[:20]}..."

    # Show first 8 characters, ellipsis, and last 4 characters
    return f"{id_str[:8]}...{id_str[-4:]}"


def validate_and_extract_notion_id(
    input_str: str, context: str = "ID"
) -> Optional[str]:
    """
    Validate and extract Notion ID from various input formats with user-friendly error messages.

    Args:
        input_str: Input string (URL or ID)
        context: Context for error messages (e.g., "Database ID", "Page ID")

    Returns:
        Validated ID or None with helpful error message
    """
    if not input_str:
        print_error(f"{context} is required")
        return None

    # Try to extract from URL first
    extracted_id = extract_notion_id_from_url(input_str)
    if extracted_id:
        print_success(f"{context} extracted from URL: {format_notion_id(extracted_id)}")
        return extracted_id

    # Check if it's already a valid ID
    if is_valid_notion_id(input_str):
        print_success(f"Valid {context}: {format_notion_id(input_str)}")
        return input_str

    # Provide helpful error message
    print_error(f"Invalid {context} format")
    print_info("Expected formats:")
    print_info(
        "   • Full URL: https://notion.so/workspace/8a021de7-2bda-434d-b255-d7cc94ebb567"
    )
    print_info("   • ID with hyphens: 8a021de7-2bda-434d-b255-d7cc94ebb567")
    print_info("   • ID without hyphens: 8a021de72bda434db255d7cc94ebb567")

    return None


def prompt_for_notion_id(
    context: str = "Notion ID", allow_url: bool = True
) -> Optional[str]:
    """
    Prompt user for a Notion ID with validation and helpful guidance.

    Args:
        context: Context for the prompt (e.g., "Database ID", "Page ID")
        allow_url: Whether to allow URL input

    Returns:
        Validated ID or None if user cancels
    """
    while True:
        if allow_url:
            prompt_text = f"Enter {context} or URL: "
        else:
            prompt_text = f"Enter {context}: "

        user_input = input(prompt_text).strip()

        # Allow user to cancel
        if user_input.lower() in ["q", "quit", "exit", "cancel"]:
            print_info("Operation cancelled by user")
            return None

        # Validate and extract
        validated_id = validate_and_extract_notion_id(user_input, context)
        if validated_id:
            return validated_id

        # Ask if user wants to try again
        retry = input("Try again? (y/n): ").lower().strip()
        if retry not in ["y", "yes"]:
            return None


def get_notion_id_from_environment(
    var_name: str = "NOTION_DATABASE_ID_POSTS",
) -> Optional[str]:
    """
    Get Notion ID from environment variable with validation.

    Args:
        var_name: Environment variable name

    Returns:
        Validated ID or None
    """
    id_str = os.environ.get(var_name)

    if not id_str:
        return None

    if is_valid_notion_id(id_str):
        return id_str

    # Try to extract from URL if it's a URL
    extracted_id = extract_notion_id_from_url(id_str)
    if extracted_id:
        # Update environment variable with extracted ID
        os.environ[var_name] = extracted_id
        return extracted_id

    return None


def display_notion_id_info(
    id_str: str, title: str = "Notion ID", show_url: bool = True
) -> None:
    """
    Display Notion ID information in a user-friendly format.

    Args:
        id_str: Notion ID to display
        title: Title for the display
        show_url: Whether to show the Notion URL
    """
    if not is_valid_notion_id(id_str):
        print_error(f"Invalid {title}: {id_str}")
        return

    print_info(f"📋 {title}:")
    print_info(f"   • ID: {id_str}")
    print_info(f"   • Short: {format_notion_id(id_str)}")

    if show_url:
        notion_url = f"https://notion.so/{id_str.replace('-', '')}"
        print_info(f"   • URL: {notion_url}")

    # Platform-specific copy command
    if os.name == "posix":  # macOS/Linux
        print_info(f"   • Copy command: echo '{id_str}' | pbcopy")
    else:  # Windows
        print_info(f"   • Copy command: echo '{id_str}' | clip")


def create_database_id_help_message() -> str:
    """
    Create a comprehensive help message for finding and using Database IDs.

    Returns:
        Formatted help message
    """
    return """
🔍 How to Find Your Notion Database ID:

1. **From Notion URL:**
   • Open your Notion database in the browser
   • Copy the URL: https://notion.so/workspace/ID-HERE
   • The ID is the last part (32 characters with hyphens)

2. **From Notion App:**
   • Right-click on your database
   • Select "Copy link"
   • Extract the ID from the copied URL

3. **Common ID Formats:**
   • With hyphens: 8a021de7-2bda-434d-b255-d7cc94ebb567
   • Without hyphens: 8a021de72bda434db255d7cc94ebb567

4. **Troubleshooting:**
   • Make sure the database is shared with your integration
   • Verify the integration has proper permissions
   • Check that you're copying the database ID, not a page ID

💡 Pro Tip: You can paste the full Notion URL and we'll extract the ID automatically!
"""


def show_database_setup_guide() -> None:
    """
    Display a step-by-step guide for setting up a Notion database.
    """
    print_info("📋 Notion Database Setup Guide:")
    print_info("")
    print_info("1. **Create a new database in Notion:**")
    print_info("   • Open Notion and create a new page")
    print_info("   • Type '/' and select 'Table' or 'Database'")
    print_info("   • Give it a name like 'Blog Posts'")
    print_info("")
    print_info("2. **Set up the database structure:**")
    print_info("   • Add columns: Name, Status, Tags, Category")
    print_info("   • Name: Title (default)")
    print_info("   • Status: Select (Draft/Published)")
    print_info("   • Tags: Multi-select")
    print_info("   • Category: Select (Tech/Life/Tutorial)")
    print_info("")
    print_info("3. **Share with your integration:**")
    print_info("   • Click 'Share' in the top right")
    print_info("   • Add your integration to the page")
    print_info("   • Grant 'Edit' permissions")
    print_info("")
    print_info("4. **Get the Database ID:**")
    print_info("   • Copy the URL from your browser")
    print_info("   • Use the ID in the setup command")
    print_info("")
    print_info("🎯 Ready to start? Run: python app.py setup --interactive")
