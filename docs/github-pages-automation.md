# GitHub Pages 자동화 설정 가이드

이 문서는 Notion-Hugo 프로젝트를 GitHub Pages에 자동으로 배포하는 방법을 설명합니다. 자동화 스크립트를 사용하여 설정 과정을 간소화할 수 있습니다.

## 개요

Notion-Hugo 프로젝트는 Notion에서 작성한 콘텐츠를 Hugo 정적 사이트 생성기로 변환하여 배포합니다. GitHub Pages는 이러한 정적 사이트를 무료로 호스팅할 수 있는 좋은 방법입니다. 

자동화 스크립트 `github-pages-setup.sh`는 다음 작업을 자동화합니다:

1. GitHub 저장소 생성 또는 연결
2. 코드 푸시
3. GitHub Pages 활성화
4. Notion API 토큰 설정
5. GitHub Actions 워크플로우 실행

## 사전 요구사항

스크립트를 실행하기 전에 다음 요구사항을 충족해야 합니다:

1. **Git**: 최신 버전의 Git이 설치되어 있어야 합니다.
2. **GitHub CLI**: 명령줄에서 GitHub API와 상호 작용하기 위한 `gh` CLI 도구가 설치되어 있어야 합니다.
   - 설치 방법: https://cli.github.com/manual/installation
3. **GitHub 계정**: 유효한 GitHub 계정이 필요합니다.
4. **GitHub CLI 로그인**: `gh auth login` 명령으로 GitHub CLI에 로그인해야 합니다.
5. **Notion API 토큰**: Notion API 통합 토큰이 설정되어 있어야 합니다.
   - `.env` 파일에 `NOTION_TOKEN=your_token_here` 형식으로 저장
   - 또는 환경 변수로 설정: `export NOTION_TOKEN=your_token_here`

## 스크립트 사용 방법

### 기본 사용법

1. 먼저 스크립트에 실행 권한을 부여합니다:

```bash
chmod +x scripts/github-pages-setup.sh
```

2. 프로젝트 루트 디렉토리에서 스크립트를 실행합니다:

```bash
./scripts/github-pages-setup.sh
```

기본적으로 이 스크립트는 GitHub API를 통해 사용자 이름을 가져와 `username.github.io` 형식의 저장소 이름을 생성합니다.

### 사용자 지정 저장소 이름 사용

특정 저장소 이름을 사용하려면 명령줄 인수로 전달하세요:

```bash
./scripts/github-pages-setup.sh custom-repo-name
```

또는 환경 변수로 설정할 수도 있습니다:

```bash
export REPO_NAME=custom-repo-name
./scripts/github-pages-setup.sh
```

## 작동 방식

스크립트는 다음 단계로 실행됩니다:

1. **필수 도구 확인**: Git과 GitHub CLI가 설치되어 있고 사용자가 로그인되어 있는지 확인합니다.
2. **환경 설정**: `.env` 파일에서 환경 변수를 로드하고 저장소 이름을 설정합니다.
3. **저장소 설정**: 저장소가 존재하는지 확인하고, 없으면 생성합니다. 원격 저장소를 설정합니다.
4. **코드 푸시**: 코드를 GitHub 저장소에 푸시합니다. 충돌이 있는 경우 옵션을 제공합니다.
5. **GitHub Pages 설정**: GitHub API를 사용하여 GitHub Pages를 활성화합니다.
6. **Notion API 토큰 설정**: GitHub 시크릿에 Notion API 토큰을 설정합니다.
7. **워크플로우 실행**: Hugo 빌드 및 Notion 동기화 워크플로우를 실행합니다.

## 문제 해결

### 일반적인 문제

#### 1. GitHub CLI 인증 오류

오류: `You are not logged in to GitHub CLI.`

해결방법: GitHub CLI에 로그인합니다.

```bash
gh auth login
```

#### 2. Notion API 토큰 누락

오류: `NOTION_TOKEN is not set.`

해결방법: `.env` 파일에 토큰을 설정하거나 환경 변수로 내보냅니다.

```bash
echo "NOTION_TOKEN=your_token_here" > .env
# 또는
export NOTION_TOKEN=your_token_here
```

#### 3. 저장소 충돌

오류: `Push failed. This might be due to unrelated histories...`

해결방법: 스크립트가 제공하는 옵션을 따르세요. 강제 푸시를 선택하면 원격 콘텐츠가 덮어쓰여집니다.

#### 4. GitHub Pages API 오류

경고: `Could not configure GitHub Pages via API.`

해결방법: GitHub 저장소 설정에서 Pages를 수동으로 활성화하세요:
1. `https://github.com/username/repo-name/settings/pages`로 이동
2. "Build and deployment"에서 "GitHub Actions"를 소스로 선택

## 수동 설정 방법

자동화 스크립트를 사용하지 않고 수동으로 설정하려면 다음 단계를 따르세요:

1. GitHub에서 새 저장소를 생성합니다. 이름: `username.github.io`
2. 로컬 저장소를 원격 저장소에 연결합니다:
   ```bash
   git remote add origin https://github.com/username/username.github.io.git
   git push -u origin main
   ```
3. GitHub 저장소 설정에서 Pages를 활성화합니다:
   - Settings > Pages > Build and deployment에서 GitHub Actions를 소스로 선택
4. GitHub 저장소에 Notion API 토큰을 시크릿으로 추가합니다:
   - Settings > Secrets and variables > Actions > New repository secret
   - Name: `NOTION_TOKEN`
   - Secret: Notion API 토큰 
5. GitHub Actions 워크플로우를 수동으로 실행합니다:
   - Actions 탭에서 워크플로우를 선택하고 "Run workflow" 버튼을 클릭

## 참고 자료

- [GitHub Pages 문서](https://docs.github.com/en/pages)
- [GitHub CLI 문서](https://cli.github.com/manual/)
- [Notion API 문서](https://developers.notion.com/)
- [Hugo 문서](https://gohugo.io/documentation/)
