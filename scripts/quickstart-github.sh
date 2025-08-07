#!/bin/bash
# Quick setup script for GitHub Pages deployment
# This script automates the entire setup process for Notion-Hugo Flow

set -e

# Ensure we're in the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🚀 Notion-Hugo Flow Quick Setup for GitHub Pages"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed."
    echo "Please install Git and try again."
    exit 1
fi

# Get Notion token
read -p "Enter your Notion API token: " NOTION_TOKEN
if [ -z "$NOTION_TOKEN" ]; then
    echo "❌ Notion token is required"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing dependencies..."
pip3 install -r dev/requirements.txt

# Run quickstart with error handling
echo "🔧 Running smart configuration..."
if ! python3 app.py quickstart --token "$NOTION_TOKEN"; then
    echo ""
    echo "⚠️  Setup encountered issues. This might be due to:"
    echo "   - Invalid Notion API token"
    echo "   - Missing Notion integration permissions"
    echo "   - Network connectivity issues"
    echo ""
    echo "🔧 Troubleshooting options:"
    echo "1. Try interactive mode: python3 app.py quickstart --token \"$NOTION_TOKEN\" --interactive"
    echo "2. Check your Notion integration permissions at: https://www.notion.so/my-integrations"
    echo "3. Ensure your integration has access to the workspace"
    echo ""
    echo "Continue with GitHub setup anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Please fix the issues and try again."
        exit 1
    fi
fi

# Git operations
echo "📝 Preparing for GitHub deployment..."
git add .
git commit -m "Initial Notion-Hugo Flow setup with GitHub Pages configuration" || true

# Final instructions
echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to your GitHub repository settings"
echo "2. Navigate to Settings → Secrets and variables → Actions"
echo "3. Add a new secret:"
echo "   Name: NOTION_TOKEN"
echo "   Value: $NOTION_TOKEN"
echo ""
echo "4. Push your changes:"
echo "   git push origin main"
echo ""
echo "5. Your blog will be live at:"
REPO_URL=$(git config --get remote.origin.url)
if [[ $REPO_URL == *".github.io"* ]]; then
    echo "   https://$(basename $REPO_URL .git)"
else
    USERNAME=$(echo $REPO_URL | sed -e 's/.*github.com[:/]\([^/]*\).*/\1/')
    REPONAME=$(basename $REPO_URL .git)
    echo "   https://$USERNAME.github.io/$REPONAME"
fi
echo ""
echo "🎉 Happy blogging with Notion-Hugo Flow!"
