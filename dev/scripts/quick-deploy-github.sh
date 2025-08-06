#!/bin/bash

# Notion-Hugo GitHub Pages 원클릭 배포 스크립트
# 사용법: curl -sSL https://raw.githubusercontent.com/adalgu/notion-hugo-py/main/scripts/quick-deploy-github.sh | bash

set -e

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display messages with colors
print_message() {
  case $1 in
    "info") echo -e "${BLUE}[INFO]${NC} $2" ;;
    "success") echo -e "${GREEN}[SUCCESS]${NC} $2" ;;
    "warning") echo -e "${YELLOW}[WARNING]${NC} $2" ;;
    "error") echo -e "${RED}[ERROR]${NC} $2" ;;
    "prompt") echo -e "${CYAN}[INPUT]${NC} $2" ;;
    *) echo -e "$2" ;;
  esac
}

# Welcome message
show_welcome() {
  echo
  echo -e "${CYAN}🚀 Notion-Hugo GitHub Pages 원클릭 배포${NC}"
  echo -e "${CYAN}=======================================${NC}"
  echo
  print_message "info" "이 스크립트는 다음 작업을 자동으로 수행합니다:"
  echo "  1. 📁 Notion-Hugo 프로젝트 클론"
  echo "  2. 📦 Python 의존성 설치"
  echo "  3. 🔑 노션 API 토큰 설정"
  echo "  4. 🏗️  노션 데이터베이스 자동 생성"
  echo "  5. 🚀 GitHub Pages 자동 배포 설정"
  echo
}

# Get Notion token from user
get_notion_token() {
  print_message "prompt" "노션 API 토큰을 입력해주세요:"
  print_message "info" "토큰이 없다면 https://notion.so/my-integrations 에서 생성하세요"
  echo -n "노션 토큰: "
  read -r NOTION_TOKEN
  
  if [ -z "$NOTION_TOKEN" ]; then
    print_message "error" "노션 토큰이 필요합니다!"
    exit 1
  fi
  
  # Validate token format
  if [[ ! "$NOTION_TOKEN" =~ ^ntn_ ]]; then
    print_message "error" "올바른 노션 토큰 형식이 아닙니다 (secret_로 시작해야 함)"
    exit 1
  fi
  
  print_message "success" "노션 토큰이 확인되었습니다!"
}

# Check if required tools are installed
check_requirements() {
  print_message "info" "시스템 요구사항 확인 중..."
  
  # Check Python
  if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_message "error" "Python이 설치되어 있지 않습니다."
    print_message "info" "Python 3.8+ 설치 후 다시 실행해주세요."
    exit 1
  fi
  
  # Use python3 if available, otherwise python
  if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
  else
    PYTHON_CMD="python"
    PIP_CMD="pip"
  fi
  
  # Check Python version
  PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
  if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    print_message "error" "Python 3.8+ 이 필요합니다. 현재 버전: $PYTHON_VERSION"
    exit 1
  fi
  
  # Check Git
  if ! command -v git &> /dev/null; then
    print_message "error" "Git이 설치되어 있지 않습니다."
    exit 1
  fi
  
  # Check GitHub CLI
  if ! command -v gh &> /dev/null; then
    print_message "warning" "GitHub CLI가 설치되어 있지 않습니다."
    print_message "info" "GitHub CLI를 설치하면 더 편리하게 사용할 수 있습니다."
    print_message "info" "설치 방법: https://cli.github.com/"
    HAS_GH_CLI=false
  else
    HAS_GH_CLI=true
  fi
  
  print_message "success" "시스템 요구사항 확인 완료!"
}

# Clone the repository
clone_repository() {
  print_message "info" "Notion-Hugo 프로젝트 클론 중..."
  
  REPO_DIR="notion-hugo-blog"
  if [ -d "$REPO_DIR" ]; then
    print_message "warning" "디렉토리 '$REPO_DIR' 이미 존재합니다."
    echo -n "기존 디렉토리를 삭제하고 계속하시겠습니까? (y/n): "
    read -r REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      rm -rf "$REPO_DIR"
    else
      print_message "error" "배포가 중단되었습니다."
      exit 1
    fi
  fi
  
  if git clone https://github.com/adalgu/notion-hugo-py.git "$REPO_DIR"; then
    print_message "success" "프로젝트 클론 완료!"
  else
    print_message "error" "프로젝트 클론에 실패했습니다."
    exit 1
  fi
}

# Install Python dependencies
install_dependencies() {
  print_message "info" "Python 의존성 설치 중..."
  
  cd "$REPO_DIR"
  
  # Try to create virtual environment
  if $PYTHON_CMD -m venv venv 2>/dev/null; then
    print_message "info" "가상환경 생성 및 활성화 중..."
    source venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
  else
    print_message "warning" "가상환경 생성에 실패했습니다. 시스템 Python을 사용합니다."
  fi
  
  # Install dependencies
  if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
  else
    # Fallback to manual installation
    $PIP_CMD install notion-client pyyaml requests python-frontmatter python-dateutil
  fi
  
  print_message "success" "Python 의존성 설치 완료!"
}

# Setup environment and Notion database
setup_notion() {
  print_message "info" "노션 환경 설정 중..."
  
  # Create .env file
  echo "NOTION_TOKEN=$NOTION_TOKEN" > .env
  
  # Run the setup script
  if $PYTHON_CMD setup.py --token "$NOTION_TOKEN" --deploy github-pages --auto-yes; then
    print_message "success" "노션 데이터베이스 및 GitHub Pages 설정 완료!"
  else
    print_message "error" "노션 설정에 실패했습니다."
    print_message "info" "수동으로 설정을 시도합니다..."
    
    # Fallback to manual setup
    if $PYTHON_CMD notion_hugo_app.py -i; then
      print_message "success" "수동 설정이 완료되었습니다!"
    else
      print_message "error" "설정에 실패했습니다. 로그를 확인해주세요."
      exit 1
    fi
  fi
}

# Get repository name for GitHub Pages
get_repo_name() {
  if [ "$HAS_GH_CLI" = true ] && gh auth status &> /dev/null; then
    USERNAME=$(gh api user | jq -r .login 2>/dev/null || gh api user --jq .login 2>/dev/null)
    if [ -n "$USERNAME" ] && [ "$USERNAME" != "null" ]; then
      REPO_NAME="${USERNAME}.github.io"
      print_message "info" "GitHub 사용자명: $USERNAME"
      print_message "info" "사용할 저장소: $REPO_NAME"
      return
    fi
  fi
  
  print_message "prompt" "GitHub 사용자명을 입력해주세요:"
  echo -n "GitHub 사용자명: "
  read -r USERNAME
  
  if [ -z "$USERNAME" ]; then
    print_message "error" "GitHub 사용자명이 필요합니다!"
    exit 1
  fi
  
  REPO_NAME="${USERNAME}.github.io"
}

# Setup GitHub repository and deploy
setup_github_deployment() {
  print_message "info" "GitHub 저장소 및 배포 설정 중..."
  
  get_repo_name
  
  # Initialize git if not already
  if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial commit: Notion-Hugo blog setup"
  fi
  
  # Setup GitHub repository
  if [ "$HAS_GH_CLI" = true ]; then
    print_message "info" "GitHub CLI를 사용하여 자동 배포 설정 중..."
    bash scripts/github-pages-setup.sh "$REPO_NAME"
  else
    print_message "info" "수동 GitHub 설정 가이드:"
    echo "1. GitHub에서 새 저장소 '$REPO_NAME' 생성"
    echo "2. 다음 명령어 실행:"
    echo "   git remote add origin https://github.com/$USERNAME/$REPO_NAME.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo "3. 저장소 Settings → Pages에서 GitHub Actions 소스 선택"
    echo "4. Secrets에 NOTION_TOKEN 추가"
  fi
}

# Show completion summary
show_completion() {
  echo
  print_message "success" "🎉 배포 완료!"
  echo
  print_message "info" "=== 📋 배포 정보 ==="
  print_message "success" "프로젝트 디렉토리: $(pwd)"
  print_message "success" "GitHub 저장소: https://github.com/$USERNAME/$REPO_NAME"
  print_message "success" "블로그 URL: https://$REPO_NAME"
  echo
  print_message "info" "=== 📝 다음 단계 ==="
  print_message "info" "1. 노션에서 블로그 포스트 작성"
  print_message "info" "2. 'isPublished' 체크박스 체크"
  print_message "info" "3. 2-3분 후 블로그에 자동 반영!"
  echo
  print_message "info" "=== 🔧 유용한 명령어 ==="
  echo "  • 수동 동기화: $PYTHON_CMD notion_hugo_app.py"
  echo "  • 전체 재빌드: $PYTHON_CMD notion_hugo_app.py --full-sync"
  echo "  • 로컬 미리보기: hugo server"
  echo
  print_message "success" "축하합니다! 노션 블로그가 준비되었습니다! 🚀"
}

# Main execution
main() {
  show_welcome
  
  # Check if running from curl
  if [ -t 0 ]; then
    # Interactive mode
    get_notion_token
  else
    print_message "error" "이 스크립트는 대화형 모드에서만 실행할 수 있습니다."
    print_message "info" "다음과 같이 실행해주세요:"
    print_message "info" "wget https://raw.githubusercontent.com/adalgu/notion-hugo-py/main/scripts/quick-deploy-github.sh"
    print_message "info" "chmod +x quick-deploy-github.sh"
    print_message "info" "./quick-deploy-github.sh"
    exit 1
  fi
  
  check_requirements
  clone_repository
  install_dependencies
  setup_notion
  setup_github_deployment
  show_completion
}

# Check if script is being executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
