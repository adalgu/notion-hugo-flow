import os
import sys
import subprocess
from dotenv import load_dotenv


def install_dependencies():
    """Install necessary dependencies if they are not already installed."""
    dependencies = ["notion-client", "python-dotenv", "pyyaml", "fs", "tabulate"]
    for dep in dependencies:
        try:
            module_name = dep.replace("-", "_")
            if module_name == "pyyaml":
                module_name = "yaml"
            __import__(module_name)
        except ImportError:
            print(f"📦 Installing {dep}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
            )


def main():
    """
    Vercel-specific setup script.
    Checks for NOTION_DATABASE_ID_POSTS. If not found, it runs the setup,
    prints the new DB ID, and exits, causing the build to fail.
    The user then adds the printed ID as an environment variable in Vercel.
    """
    load_dotenv()
    install_dependencies()

    from setup import OneStopInstaller

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")

    if not notion_token:
        print(
            "❌ ERROR: NOTION_TOKEN environment variable is not set in Vercel.",
            file=sys.stderr,
        )
        sys.exit(1)

    if database_id:
        print("✅ NOTION_DATABASE_ID_POSTS found. Skipping setup.")
        sys.exit(0)
    else:
        print(
            "ℹ️ NOTION_DATABASE_ID_POSTS not found. Starting one-time database setup..."
        )

        installer = OneStopInstaller(notion_token, interactive=False)

        # Run only the necessary parts of the installation
        is_valid, message = installer.validate_notion_token()
        if not is_valid:
            print(f"❌ Token validation failed: {message}", file=sys.stderr)
            sys.exit(1)

        print("✅ Token validated.")

        permissions = installer.detect_notion_permissions()
        if not permissions.get("can_create_database"):
            print(
                "❌ Notion integration does not have permission to create databases.",
                file=sys.stderr,
            )
            sys.exit(1)

        print("✅ Permissions checked.")

        db_result = installer.create_optimized_database(permissions)
        if not db_result.get("success"):
            print(
                f"❌ Failed to create database: {db_result.get('error')}",
                file=sys.stderr,
            )
            sys.exit(1)

        new_db_id = db_result.get("database_id")
        print(f"✅ New database created: {new_db_id}")

        installer.database_id = new_db_id
        posts_result = installer.create_sample_posts()
        if not posts_result.get("success"):
            print(
                f"⚠️ Failed to create sample posts, but database was created.",
                file=sys.stderr,
            )

        print("\n" + "=" * 60)
        print("🛑 ACTION REQUIRED: Vercel Setup Incomplete")
        print("=" * 60)
        print("A new Notion database has been created for your project.")
        print("You must now add this database ID as an environment variable")
        print("to your Vercel project settings to complete the setup.")
        print("\n1. Go to your Vercel Project -> Settings -> Environment Variables.")
        print("2. Add a new variable with the following details:")
        print(f"   - Key: NOTION_DATABASE_ID_POSTS")
        print(f"   - Value: {new_db_id}")
        print("3. Ensure the variable is available for the Production environment.")
        print("4. After adding the variable, re-deploy the project.")
        print(
            "\nThis build will now fail. This is expected. Please follow the steps above."
        )
        print("=" * 60 + "\n")

        # Exit with an error code to stop the current build
        sys.exit(1)


if __name__ == "__main__":
    main()
