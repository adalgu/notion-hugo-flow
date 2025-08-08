# 새로운 Notion-Hugo 파이프라인 아키텍처

## 🎯 핵심 철학

**"단순함이 최고의 복잡함이다"**

기존의 복잡하고 혼란스러운 구조를 완전히 버리고, 각 단계가 명확한 책임을 가진 독립적인 파이프라인으로 재설계합니다.

## 📊 파이프라인 구조 개요

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NOTION        │    │     HUGO        │    │   DEPLOYMENT    │
│   PIPELINE      │───▶│   PIPELINE      │───▶│   PIPELINE      │
│                 │    │                 │    │                 │
│ Input: Token    │    │ Input: MD Files │    │ Input: Site     │
│ Output: MD      │    │ Output: Site    │    │ Output: Live    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 1단계: NOTION PIPELINE

### 목적
Notion 데이터를 Hugo 호환 마크다운으로 변환

### Input
```yaml
notion_pipeline:
  input:
    token: "ntn_..."                    # Notion API 토큰
    database_id: "..."                  # 데이터베이스 ID
    sync_mode: "incremental"            # incremental | full
    filters:
      status: ["Published", "Live"]     # 상태 필터
      date_range:                       # 날짜 범위 (선택)
        from: "2024-01-01"
        to: null
```

### Output
```yaml
notion_pipeline:
  output:
    markdown_files:                     # 생성된 마크다운 파일들
      - path: "blog/content/posts/post-1.md"
        metadata:
          title: "Post Title"
          date: "2024-01-15"
          tags: ["tech", "ai"]
          status: "published"
    sync_state:                         # 동기화 상태
      last_sync: "2024-01-15T10:30:00Z"
      processed_count: 25
      new_files: 3
      updated_files: 2
      deleted_files: 0
    errors: []                          # 오류 목록
```

### 명령어
```bash
# 기본 동기화
python notion.py sync

# 전체 동기화
python notion.py sync --full

# 특정 데이터베이스만
python notion.py sync --database-id "xxx"

# 드라이 런
python notion.py sync --dry-run
```

## 🏗️ 2단계: HUGO PIPELINE

### 목적
마크다운 파일을 Hugo 사이트로 빌드

### Input
```yaml
hugo_pipeline:
  input:
    content_dir: "blog/content"         # 콘텐츠 디렉토리
    config_file: "blog/config.yaml"     # Hugo 설정 파일
    theme: "PaperMod"                   # 사용할 테마
    build_mode: "production"            # production | development
    options:
      minify: true                      # 파일 압축
      enable_git_info: true             # Git 정보 포함
      build_drafts: false               # 초안 빌드 안함
```

### Output
```yaml
hugo_pipeline:
  output:
    site_directory: "blog/public"       # 빌드된 사이트
    build_info:
      build_time: "2024-01-15T10:35:00Z"
      total_pages: 25
      total_sections: 3
      build_duration: "2.3s"
    assets:
      css_files: 5
      js_files: 3
      images: 12
    errors: []                          # 빌드 오류
```

### 명령어
```bash
# 기본 빌드
python hugo.py build

# 개발 서버 시작
python hugo.py serve

# 프로덕션 빌드
python hugo.py build --production

# 특정 테마로 빌드
python hugo.py build --theme "PaperMod"
```

## 🚀 3단계: DEPLOYMENT PIPELINE

### 목적
빌드된 사이트를 실제 서비스에 배포

### Input
```yaml
deployment_pipeline:
  input:
    site_directory: "blog/public"       # 배포할 사이트
    platform: "github_pages"            # github_pages | vercel | netlify
    credentials:
      github_token: "ghp_..."           # GitHub 토큰
      repository: "username/repo"       # 저장소 정보
    options:
      auto_deploy: true                 # 자동 배포
      custom_domain: "example.com"      # 커스텀 도메인
```

### Output
```yaml
deployment_pipeline:
  output:
    deployment_url: "https://username.github.io/repo"
    deployment_time: "2024-01-15T10:40:00Z"
    status: "success"                   # success | failed | pending
    details:
      files_uploaded: 156
      total_size: "2.3MB"
      cache_invalidated: true
    errors: []                          # 배포 오류
```

### 명령어
```bash
# GitHub Pages 배포
python deploy.py github

# Vercel 배포
python deploy.py vercel

# 배포 상태 확인
python deploy.py status

# 드라이 런
python deploy.py github --dry-run
```

## 🔧 통합 명령어 (편의성)

### 전체 파이프라인 실행
```bash
# 1단계: Notion 동기화
python notion.py sync

# 2단계: Hugo 빌드
python hugo.py build

# 3단계: 배포
python deploy.py github

# 또는 한 번에 실행
python pipeline.py run --deploy
```

### 개발 워크플로우
```bash
# 개발 모드 (자동 새로고침)
python pipeline.py dev

# 프로덕션 빌드 및 배포
python pipeline.py deploy
```

## 📁 새로운 파일 구조

```
src/
├── notion/
│   ├── __init__.py
│   ├── pipeline.py          # Notion 파이프라인
│   ├── sync.py              # 동기화 로직
│   ├── converter.py         # 마크다운 변환
│   └── config.py            # Notion 설정
├── hugo/
│   ├── __init__.py
│   ├── pipeline.py          # Hugo 파이프라인
│   ├── builder.py           # 빌드 로직
│   ├── server.py            # 개발 서버
│   └── config.py            # Hugo 설정
├── deployment/
│   ├── __init__.py
│   ├── pipeline.py          # 배포 파이프라인
│   ├── github.py            # GitHub Pages
│   ├── vercel.py            # Vercel
│   └── config.py            # 배포 설정
├── pipeline.py              # 통합 파이프라인
└── config/
    ├── notion.yaml          # Notion 설정
    ├── hugo.yaml            # Hugo 설정
    └── deployment.yaml      # 배포 설정
```

## 🎯 각 파이프라인의 독립성

### 1. 독립적 실행 가능
```bash
# Notion만 실행
python notion.py sync

# Hugo만 실행
python hugo.py build

# 배포만 실행
python deploy.py github
```

### 2. 독립적 설정
```yaml
# notion.yaml
notion:
  token: "ntn_..."
  database_id: "..."

# hugo.yaml
hugo:
  theme: "PaperMod"
  base_url: "https://example.com"

# deployment.yaml
deployment:
  platform: "github_pages"
  repository: "username/repo"
```

### 3. 독립적 오류 처리
- 각 파이프라인은 자신의 오류만 처리
- 다른 파이프라인에 영향 주지 않음
- 명확한 오류 메시지와 복구 방안 제시

## 🔄 파이프라인 간 데이터 전달

### 1. 파일 기반 전달
```
Notion Pipeline → blog/content/posts/*.md
Hugo Pipeline → blog/public/
Deployment Pipeline → blog/public/
```

### 2. 상태 파일 기반 전달
```json
// .pipeline-state.json
{
  "notion": {
    "last_sync": "2024-01-15T10:30:00Z",
    "processed_count": 25
  },
  "hugo": {
    "last_build": "2024-01-15T10:35:00Z",
    "build_success": true
  },
  "deployment": {
    "last_deploy": "2024-01-15T10:40:00Z",
    "deploy_url": "https://..."
  }
}
```

## 🚀 마이그레이션 계획

### Phase 1: 새로운 구조 생성
1. 새로운 파이프라인 구조 생성
2. 각 파이프라인 독립적 구현
3. 기본 기능 테스트

### Phase 2: 기존 기능 이전
1. 기존 app.py 기능을 각 파이프라인으로 분산
2. 설정 파일 통합 및 정리
3. 사용자 시나리오 단순화

### Phase 3: 최적화 및 개선
1. 성능 최적화
2. 오류 처리 개선
3. 사용자 경험 향상

## 💡 핵심 장점

1. **명확한 책임 분리**: 각 파이프라인이 하나의 명확한 목적
2. **독립적 개발**: 각 파이프라인을 독립적으로 개발/테스트 가능
3. **유연한 사용**: 필요한 파이프라인만 선택적 실행
4. **쉬운 디버깅**: 문제가 발생한 파이프라인만 집중 분석
5. **확장성**: 새로운 플랫폼이나 기능 추가 용이
6. **유지보수성**: 코드 구조가 단순하고 명확

이 새로운 아키텍처는 기존의 복잡함을 완전히 해결하고, 각 단계가 명확한 Input/Output을 가진 독립적인 파이프라인으로 작동합니다. 