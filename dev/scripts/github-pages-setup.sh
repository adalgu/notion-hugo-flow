#!/bin/bash

# GitHub Pages Setup Automation Script for Notion-Hugo
# Created: 2025-03-17
# Author: Notion-Hugo Development Team

set -e

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display messages with colors
print_message() {
  case $1 in
    "info") echo -e "${BLUE}[INFO]${NC} $2" ;;
    "success") echo -e "${GREEN}[SUCCESS]${NC} $2" ;;
    "warning") echo -e "${YELLOW}[WARNING]${NC} $2" ;;
    "error") echo -e "${RED}[ERROR]${NC} $2" ;;
    *) echo -e "$2" ;;
  esac
}

# Check if required tools are installed
check_requirements() {
  print_message "info" "Checking required tools..."
  
  if ! command -v git &> /dev/null; then
    print_message "error" "Git is not installed. Please install git and try again."
    exit 1
  fi
  
  if ! command -v gh &> /dev/null; then
    print_message "error" "GitHub CLI is not installed. Please install gh and try again."
    print_message "info" "Visit https://cli.github.com/manual/installation for installation instructions."
    exit 1
  fi
  
  # Check if user is logged in to GitHub CLI
  if ! gh auth status &> /dev/null; then
    print_message "error" "You are not logged in to GitHub CLI. Please run 'gh auth login' first."
    exit 1
  fi
  
  print_message "success" "All required tools are available."
}

# Load environment variables from .env file
load_env() {
  print_message "info" "Loading environment variables..."
  
  if [ -f .env ]; then
    source .env
    print_message "success" "Environment variables loaded from .env file."
  else
    print_message "warning" "No .env file found. Please make sure NOTION_TOKEN is set."
    if [ -z "$NOTION_TOKEN" ]; then
      print_message "error" "NOTION_TOKEN is not set. Please create .env file or export NOTION_TOKEN manually."
      exit 1
    fi
  fi
}

# Get repository name or use default if not provided
setup_repo_name() {
  if [ -z "$REPO_NAME" ]; then
    # Try to get username from GitHub CLI
    USERNAME=$(gh api user | jq -r .login)
    
    if [ -z "$USERNAME" ]; then
      print_message "error" "Could not determine GitHub username."
      exit 1
    fi
    
    # Default repository name is username.github.io
    REPO_NAME="${USERNAME}.github.io"
    print_message "info" "Using default repository name: $REPO_NAME"
  fi
  
  # Check if repository exists
  if gh repo view "$REPO_NAME" &> /dev/null; then
    print_message "info" "Repository $REPO_NAME already exists."
    REPO_EXISTS=true
  else
    print_message "info" "Repository $REPO_NAME does not exist and will be created."
    REPO_EXISTS=false
  fi
}

# Create or connect to the GitHub repository
setup_repository() {
  print_message "info" "Setting up repository $REPO_NAME..."
  
  # Check if we're inside a git repo
  if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    print_message "error" "Not inside a git repository. Please run this script from your project root."
    exit 1
  fi
  
  # Get current remotes
  CURRENT_REMOTE=$(git remote -v | grep origin | grep push | awk '{print $2}')
  
  if [ -z "$CURRENT_REMOTE" ]; then
    print_message "info" "No remote origin found. Adding remote origin..."
    
    if [ "$REPO_EXISTS" = false ]; then
      print_message "info" "Creating new repository $REPO_NAME..."
      gh repo create "$REPO_NAME" --public
    fi
    
    git remote add origin "https://github.com/$REPO_NAME.git"
    print_message "success" "Remote origin added: https://github.com/$REPO_NAME.git"
  else
    # If remote exists but points to a different repo
    TARGET_REMOTE="https://github.com/$REPO_NAME.git"
    if [ "$CURRENT_REMOTE" != "$TARGET_REMOTE" ]; then
      print_message "warning" "Remote origin points to $CURRENT_REMOTE instead of $TARGET_REMOTE"
      
      # Handle non-interactive mode
      if [ "$NON_INTERACTIVE" = "true" ]; then
        if [ "$AUTO_CONFIRM" = "yes" ]; then
          print_message "info" "Auto-updating remote origin in non-interactive mode..."
          git remote set-url origin "$TARGET_REMOTE"
          print_message "success" "Remote origin updated to: $TARGET_REMOTE"
        else
          print_message "warning" "Continuing with existing remote in non-interactive mode: $CURRENT_REMOTE"
          # Extract actual repo name from remote
          REPO_NAME=$(echo "$CURRENT_REMOTE" | sed -e 's/.*github.com\/\(.*\)\.git/\1/')
        fi
      else
        read -p "Do you want to update the remote origin? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
          git remote set-url origin "$TARGET_REMOTE"
          print_message "success" "Remote origin updated to: $TARGET_REMOTE"
        else
          print_message "warning" "Continuing with existing remote: $CURRENT_REMOTE"
          # Extract actual repo name from remote
          REPO_NAME=$(echo "$CURRENT_REMOTE" | sed -e 's/.*github.com\/\(.*\)\.git/\1/')
        fi
      fi
    else
      print_message "success" "Remote origin already set correctly to: $CURRENT_REMOTE"
    fi
  fi
}

# Push code to GitHub repository
push_code() {
  print_message "info" "Pushing code to repository..."
  
  # Check for uncommitted changes
  if ! git diff-index --quiet HEAD --; then
    print_message "warning" "You have uncommitted changes."
    
    # Handle non-interactive mode
    if [ "$NON_INTERACTIVE" = "true" ]; then
      if [ "$AUTO_CONFIRM" = "yes" ]; then
        print_message "info" "Auto-continuing in non-interactive mode..."
      else
        print_message "error" "Cannot proceed with uncommitted changes in non-interactive mode."
        exit 1
      fi
    else
      read -p "Do you want to continue anyway? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
      fi
    fi
  fi
  
  # Try to push, if it fails offer to force push
  if ! git push -u origin main 2>/dev/null; then
    print_message "warning" "Push failed. This might be due to unrelated histories or the remote repo having content."
    
    # Handle non-interactive mode
    if [ "$NON_INTERACTIVE" = "true" ]; then
      if [ "$FORCE_PUSH" = "yes" ]; then
        print_message "warning" "Auto-force pushing in non-interactive mode..."
        git push --force origin main
        print_message "success" "Code force pushed to repository."
      else
        print_message "error" "Push failed and FORCE_PUSH is not enabled. Aborting."
        print_message "info" "To enable force push, set FORCE_PUSH=yes environment variable."
        exit 1
      fi
    else
      read -p "Do you want to force push? This will OVERWRITE remote content! (y/n) " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push --force origin main
        print_message "success" "Code force pushed to repository."
      else
        print_message "error" "Push aborted. Please resolve the conflicts manually."
        exit 1
      fi
    fi
  else
    print_message "success" "Code pushed to repository."
  fi
}

# Configure GitHub Pages
setup_github_pages() {
  print_message "info" "Setting up GitHub Pages..."
  
  # Try to enable GitHub Pages with GitHub Actions
  if gh api repos/"$REPO_NAME"/pages -X PUT -f build_type="workflow" &>/dev/null; then
    print_message "success" "GitHub Pages enabled with GitHub Actions workflow."
  else
    print_message "warning" "Could not configure GitHub Pages via API. This might be normal for a new repository."
    print_message "info" "Please manually enable GitHub Pages in repository settings:"
    print_message "info" "1. Go to https://github.com/$REPO_NAME/settings/pages"
    print_message "info" "2. Under 'Build and deployment', select 'GitHub Actions' as source."
  fi
}

# Set up Notion API token as a GitHub secret
setup_notion_token() {
  print_message "info" "Setting up Notion API token as a GitHub secret..."
  
  if [ -z "$NOTION_TOKEN" ]; then
    print_message "error" "NOTION_TOKEN is not set. Please make sure it's in .env file or exported."
    exit 1
  fi
  
  if gh secret set NOTION_TOKEN --body "$NOTION_TOKEN" --repo "$REPO_NAME"; then
    print_message "success" "NOTION_TOKEN secret set successfully."
  else
    print_message "error" "Failed to set NOTION_TOKEN secret."
    exit 1
  fi
}

# Run GitHub Actions workflows
run_workflows() {
  print_message "info" "Running GitHub Actions workflows..."
  
  # Run Hugo build and deploy workflow with buildDrafts flag
  if gh workflow run "Deploy Hugo site to Pages" --repo "$REPO_NAME"; then
    print_message "success" "Hugo build and deploy workflow started (with buildDrafts enabled)."
  else
    print_message "warning" "Failed to start Hugo workflow. It might be named differently or not exist yet."
  fi
  
  # Run Notion sync workflow
  if gh workflow run "Notion to Hugo Sync" --repo "$REPO_NAME"; then
    print_message "success" "Notion to Hugo sync workflow started."
  else
    print_message "warning" "Failed to start Notion sync workflow. It might be named differently or not exist yet."
  fi
}

# Display summary and next steps
show_summary() {
  echo
  print_message "info" "=== Setup Summary ==="
  print_message "info" "Repository: https://github.com/$REPO_NAME"
  print_message "info" "GitHub Pages: https://${REPO_NAME/\//.github.io/}" # Replace username/reponame with username.github.io
  print_message "info" "Notion API Token: Configured as GitHub secret"
  print_message "info" "Workflows: Initiated"
  echo
  print_message "info" "=== Next Steps ==="
  print_message "info" "1. It may take a few minutes for GitHub Pages to be fully deployed."
  print_message "info" "2. You can check workflow status at: https://github.com/$REPO_NAME/actions"
  print_message "info" "3. Visit your GitHub Pages site at: https://${REPO_NAME/\//.github.io/}"
  echo
  print_message "success" "Setup completed successfully!"
}

# Main execution
main() {
  print_message "info" "Starting GitHub Pages setup for Notion-Hugo..."
  
  # Check for non-interactive mode
  if [ "$NON_INTERACTIVE" = "true" ]; then
    print_message "info" "Running in non-interactive mode..."
    print_message "info" "AUTO_CONFIRM: ${AUTO_CONFIRM:-no}"
    print_message "info" "FORCE_PUSH: ${FORCE_PUSH:-no}"
  fi
  
  check_requirements
  load_env
  setup_repo_name
  setup_repository
  push_code
  setup_github_pages
  setup_notion_token
  run_workflows
  show_summary
}

# Check if script is being executed directly or sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  # Get repo name from command line if provided
  if [ $# -gt 0 ]; then
    REPO_NAME=$1
  fi
  
  main
fi
