# GitHub Pages 자동화 스크립트 구현

- **날짜**: 2025-03-17
- **작성자**: Notion-Hugo 개발팀
- **관련 이슈**: GitHub Pages 배포 자동화
- **이전 로그**: [GitHub/Vercel CI/CD 설정](../github-vercel-cicd-setup.md)

## 문제 상황

Notion-Hugo 프로젝트를 GitHub Pages에 배포하는 과정은 여러 수동 단계를 필요로 합니다. 이 과정은 다음과 같은 작업을 포함합니다:

1. GitHub 저장소 생성 또는 연결
2. 코드를 저장소에 푸시
3. GitHub Pages 활성화
4. Notion API 토큰을 GitHub 시크릿으로 설정
5. GitHub Actions 워크플로우 실행

이러한 수동 설정 과정은 복잡하고 오류가 발생하기 쉬우며, 특히 기술에 익숙하지 않은 사용자에게는 어려울 수 있습니다. 또한 문서화만으로는 명확한 지침을 제공하기 어려운 경우가 많습니다.

## 해결 전략

이 문제를 해결하기 위해 GitHub Pages 설정 과정을 자동화하는 Bash 스크립트를 개발했습니다. 스크립트는 GitHub CLI를 활용하여 모든 필요한 단계를 자동화하고, 사용자에게 명확한 안내와 피드백을 제공합니다.

주요 해결 방법은 다음과 같습니다:

1. 사용자 친화적인 대화형 스크립트 개발
2. GitHub CLI의 API 기능 활용
3. 오류 상황에 대한 적절한 처리 및 안내
4. 상세한 문서화를 통한 사용 가이드 제공

## 구현 세부사항

### 스크립트 구조

스크립트는 모듈식으로 구성되어 있으며, 각 기능은 개별 함수로 구현되었습니다:

1. `check_requirements()`: Git, GitHub CLI 설치 및 로그인 상태 확인
2. `load_env()`: 환경 변수 로드 (특히 Notion API 토큰)
3. `setup_repo_name()`: GitHub 사용자명을 기반으로 저장소 이름 생성
4. `setup_repository()`: 저장소 생성 또는 연결
5. `push_code()`: 코드 푸시 및 충돌 처리
6. `setup_github_pages()`: GitHub Pages 활성화
7. `setup_notion_token()`: Notion API 토큰을 GitHub 시크릿으로 설정
8. `run_workflows()`: GitHub Actions 워크플로우 실행
9. `show_summary()`: 설정 결과 요약 및 다음 단계 안내

사용자 경험을 향상시키기 위해 컬러 출력과 명확한 메시지를 통해 진행 상황을 안내합니다.

### 핵심 코드 예시

GitHub Pages 설정 함수:

```bash
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
```

Notion API 토큰 설정 함수:

```bash
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
```

### 문서화

스크립트 사용 방법을 상세히 설명하는 문서 `docs/github-pages-automation.md`를 작성했습니다. 이 문서는 다음 내용을 포함합니다:

- 개요 및 기능 설명
- 사전 요구사항
- 기본 및 고급 사용법
- 작동 방식 설명
- 문제 해결 가이드
- 수동 설정 방법 (스크립트를 사용할 수 없는 경우)
- 참고 자료

## 기술적 고려사항

### GitHub API 접근 방법

GitHub API를 직접 호출하는 대신 GitHub CLI를 활용했습니다. 이는 사용자 인증, 오류 처리, 진행 상황 표시 등의 기능을 제공하여 스크립트 작성을 단순화했습니다.

GitHub CLI는 다음과 같은 이점을 제공합니다:
- 사용자의 GitHub 계정 정보를 안전하게 관리
- 다양한 GitHub 기능에 대한 일관된 인터페이스
- 로그인 상태 및 권한 관리 기능

### 보안 고려사항

Notion API 토큰과 같은 민감한 정보를 처리할 때 보안을 최우선으로 고려했습니다:

1. 환경 변수나 `.env` 파일에서 토큰을 읽어오도록 함
2. GitHub 시크릿으로 안전하게 저장
3. 토큰 값이 출력 로그에 노출되지 않도록 주의

### 오류 처리 및 회복성

다양한 오류 상황에 대응하도록 스크립트를 설계했습니다:

1. 필수 도구 누락 시 명확한 오류 메시지와 설치 지침 제공
2. 저장소 충돌 발생 시 사용자에게 옵션 제시
3. API 호출 실패 시 대체 방법 안내
4. 각 단계에서 발생할 수 있는 오류에 대한 문제 해결 지침 문서화

## 다음 단계

자동화 스크립트의 추가 개선 가능성:

1. **멀티 플랫폼 지원**: Windows 환경(Git Bash, WSL)에서의 추가 테스트 및 호환성 보장
2. **비대화식 모드**: CI/CD 환경에서 활용할 수 있는 비대화식 모드 추가
3. **시스템 통합**: 메인 Notion-Hugo CLI에 GitHub Pages 배포 옵션으로 통합
4. **자동 업데이트 확인**: 스크립트 업데이트 확인 및 자동 업데이트 기능
5. **더 많은 배포 옵션**: Vercel, Netlify 등 다른 배포 플랫폼에 대한 지원 확장

## 참고 자료

- [GitHub CLI API 문서](https://cli.github.com/manual/gh_api)
- [GitHub Pages API 문서](https://docs.github.com/en/rest/pages)
- [Bash 스크립트 작성 가이드](https://tldp.org/LDP/abs/html/)
- [GitHub Actions 워크플로우 문서](https://docs.github.com/en/actions/using-workflows)
