# 파이프라인 Input-Output 명세표

## 🎯 핵심 원칙

**"단순하고 명확한 책임 분리"**

각 파이프라인은 하나의 명확한 목적만 가지고, Input을 받아서 Output을 생성합니다. 파이프라인 간의 의존성은 파일 시스템을 통해서만 이루어집니다.

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

---

## 🔄 1단계: NOTION PIPELINE

### 목적
Notion 데이터를 Hugo 호환 마크다운으로 변환

### Input 명세
```yaml
notion_pipeline_input:
  # 필수 입력
  token: "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"
  database_id: "2487522e-eb2f-815a-97b1-e035f30f83ea"
  
  # 선택적 입력
  sync_mode: "incremental"              # incremental | full
  batch_size: 50                        # 1-100
  include_drafts: false                 # true | false
  
  # 필터 설정
  filters:
    status: ["Published", "Live"]       # 게시 상태 필터
    date_range:                         # 날짜 범위 (선택)
      from: "2024-01-01"
      to: null
  
  # 출력 설정
  output_dir: "blog/content/posts"      # 마크다운 파일 저장 위치
  markdown_format: "hugo"               # hugo | standard
```

### Output 명세
```yaml
notion_pipeline_output:
  # 생성된 파일들
  markdown_files:
    - path: "blog/content/posts/2024-01-15-my-first-post.md"
      metadata:
        title: "My First Post"
        date: "2024-01-15T10:30:00Z"
        tags: ["tech", "ai"]
        categories: ["Technology"]
        status: "published"
        notion_id: "page_id_here"
      content: |
        # My First Post
        
        This is the content of my first post...
  
  # 동기화 상태
  sync_state:
    last_sync: "2024-01-15T10:30:00Z"
    processed_count: 25
    new_files: 3
    updated_files: 2
    deleted_files: 0
    errors: []
  
  # 성능 정보
  performance:
    sync_duration: "2.3s"
    api_calls: 15
    rate_limit_remaining: 85
```

### 명령어
```bash
# 기본 동기화
python notion.py sync

# 전체 동기화
python notion.py sync --full

# 특정 데이터베이스만
python notion.py sync --database-id "xxx"

# 드라이 런 (실제 파일 생성 안함)
python notion.py sync --dry-run

# 상태 확인
python notion.py status
```

---

## 🏗️ 2단계: HUGO PIPELINE

### 목적
마크다운 파일을 Hugo 사이트로 빌드

### Input 명세
```yaml
hugo_pipeline_input:
  # 콘텐츠 입력
  content_dir: "blog/content"           # 마크다운 파일 위치
  static_dir: "blog/static"             # 정적 파일 위치
  layouts_dir: "blog/layouts"           # 레이아웃 파일 위치
  
  # 설정 파일
  config_file: "blog/config.yaml"       # Hugo 설정 파일
  theme: "PaperMod"                     # 사용할 테마
  
  # 빌드 옵션
  build_mode: "production"              # production | development
  minify: true                          # 파일 압축
  enable_git_info: true                 # Git 정보 포함
  build_drafts: false                   # 초안 빌드 안함
  build_future: false                   # 미래 날짜 빌드 안함
  
  # 서버 옵션 (개발 모드)
  server:
    port: 1313
    host: "localhost"
    watch: true                         # 파일 변경 감지
```

### Output 명세
```yaml
hugo_pipeline_output:
  # 빌드된 사이트
  site_directory: "blog/public"
  
  # 빌드 정보
  build_info:
    build_time: "2024-01-15T10:35:00Z"
    build_duration: "2.3s"
    total_pages: 25
    total_sections: 3
    build_success: true
  
  # 생성된 파일들
  generated_files:
    html_files: 28
    css_files: 5
    js_files: 3
    images: 12
    other_files: 8
  
  # 사이트 구조
  site_structure:
    pages:
      - path: "/"
        title: "Home"
        type: "home"
      - path: "/posts/"
        title: "Posts"
        type: "list"
      - path: "/posts/my-first-post/"
        title: "My First Post"
        type: "single"
    
    sections:
      - name: "posts"
        count: 25
        path: "/posts/"
    
    taxonomies:
      tags: 15
      categories: 8
  
  # 성능 정보
  performance:
    total_size: "2.3MB"
    compression_ratio: 0.75
    build_errors: []
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

# 빌드 상태 확인
python hugo.py status
```

---

## 🚀 3단계: DEPLOYMENT PIPELINE

### 목적
빌드된 사이트를 실제 서비스에 배포

### Input 명세
```yaml
deployment_pipeline_input:
  # 배포할 사이트
  site_directory: "blog/public"         # Hugo가 빌드한 사이트
  
  # 플랫폼 설정
  platform: "github_pages"              # github_pages | vercel | netlify
  
  # GitHub Pages 설정
  github:
    token: "ghp_..."                    # GitHub Personal Access Token
    repository: "username/repo"         # 저장소 정보
    branch: "gh-pages"                  # 배포 브랜치
    custom_domain: "example.com"        # 커스텀 도메인 (선택)
  
  # Vercel 설정 (대안)
  vercel:
    token: "vercel_token"
    project_id: "project_id"
    team_id: "team_id"
  
  # 배포 옵션
  options:
    auto_deploy: true                   # 자동 배포
    cache_invalidation: true            # 캐시 무효화
    compression: true                   # 파일 압축
    cdn_enabled: true                   # CDN 사용
```

### Output 명세
```yaml
deployment_pipeline_output:
  # 배포 결과
  deployment:
    url: "https://username.github.io/repo"
    status: "success"                   # success | failed | pending
    deployment_time: "2024-01-15T10:40:00Z"
    deployment_id: "deploy_123456"
  
  # 배포 상세 정보
  details:
    files_uploaded: 156
    total_size: "2.3MB"
    cache_invalidated: true
    cdn_propagation: "completed"
  
  # 성능 정보
  performance:
    upload_duration: "45s"
    build_duration: "2.3s"
    total_duration: "47.3s"
  
  # 모니터링 정보
  monitoring:
    response_time: "120ms"
    availability: "99.9%"
    ssl_status: "valid"
  
  # 오류 정보
  errors: []                            # 배포 중 발생한 오류
```

### 명령어
```bash
# GitHub Pages 배포
python deploy.py github

# Vercel 배포
python deploy.py vercel

# 배포 상태 확인
python deploy.py status

# 드라이 런 (실제 배포 안함)
python deploy.py github --dry-run

# 배포 히스토리 확인
python deploy.py history
```

---

## 🔧 통합 워크플로우

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

---

## 📋 사용 시나리오별 Input-Output 매핑

### 시나리오 1: 초기 설치 및 설정

#### Input
```yaml
initial_setup_input:
  notion_token: "ntn_..."
  # database_id는 자동 생성됨
  target_folder: "posts"
  theme: "PaperMod"
  deploy_platform: "github_pages"
```

#### Output
```yaml
initial_setup_output:
  # 생성된 파일들
  files:
    - "src/config/notion.yaml"          # Notion 설정
    - "src/config/hugo.yaml"            # Hugo 설정
    - "src/config/deployment.yaml"      # 배포 설정
    - "blog/content/posts/sample-1.md"  # 샘플 포스트
    - "blog/content/posts/sample-2.md"  # 샘플 포스트
  
  # 설정 정보
  configuration:
    notion_database_id: "auto_generated_id"
    hugo_site_url: "http://localhost:1313"
    deployment_url: "https://username.github.io/repo"
  
  # 상태 정보
  status:
    setup_complete: true
    sample_posts_created: 2
    local_server_running: true
    deployment_ready: true
```

### 시나리오 2: 일상적인 콘텐츠 업데이트

#### Input
```yaml
content_update_input:
  # Notion에서 새 포스트 작성 후
  sync_mode: "incremental"
  # 또는 전체 동기화
  sync_mode: "full"
```

#### Output
```yaml
content_update_output:
  # 변경된 파일들
  changes:
    new_posts: 1
    updated_posts: 0
    deleted_posts: 0
  
  # 빌드 결과
  build:
    total_pages: 26  # 25 + 1
    build_success: true
  
  # 배포 결과
  deployment:
    status: "success"
    url: "https://username.github.io/repo"
    deployment_time: "2024-01-15T11:00:00Z"
```

### 시나리오 3: 백업 및 복구

#### Input
```yaml
backup_input:
  backup_mode: "full"                   # full | incremental
  backup_location: "backup/content"     # 로컬 백업
  # 또는
  backup_location: "remote/git"         # 원격 Git 저장소
```

#### Output
```yaml
backup_output:
  # 백업된 파일들
  backup_files:
    markdown_files: 25
    config_files: 3
    total_size: "1.2MB"
  
  # 백업 정보
  backup_info:
    backup_time: "2024-01-15T12:00:00Z"
    backup_location: "backup/content"
    backup_success: true
  
  # 복구 정보
  recovery_info:
    recovery_available: true
    recovery_point: "2024-01-15T12:00:00Z"
    recovery_instructions: "python backup.py restore --point 2024-01-15T12:00:00Z"
```

---

## 🔄 파이프라인 간 데이터 전달

### 파일 기반 전달
```
Notion Pipeline Output → Hugo Pipeline Input
├── blog/content/posts/*.md
├── blog/content/pages/*.md
└── .notion-sync-state.json

Hugo Pipeline Output → Deployment Pipeline Input
└── blog/public/
    ├── index.html
    ├── posts/
    ├── assets/
    └── sitemap.xml
```

### 상태 파일 기반 전달
```json
// .pipeline-state.json
{
  "notion": {
    "last_sync": "2024-01-15T10:30:00Z",
    "processed_count": 25,
    "sync_success": true
  },
  "hugo": {
    "last_build": "2024-01-15T10:35:00Z",
    "build_success": true,
    "total_pages": 25
  },
  "deployment": {
    "last_deploy": "2024-01-15T10:40:00Z",
    "deploy_success": true,
    "deploy_url": "https://username.github.io/repo"
  }
}
```

---

## 🎯 핵심 장점

1. **명확한 책임 분리**: 각 파이프라인이 하나의 명확한 목적
2. **독립적 실행**: 각 파이프라인을 독립적으로 실행 가능
3. **명확한 Input/Output**: 각 단계의 입출력이 명확히 정의됨
4. **쉬운 디버깅**: 문제가 발생한 파이프라인만 집중 분석
5. **유연한 사용**: 필요한 파이프라인만 선택적 실행
6. **확장성**: 새로운 플랫폼이나 기능 추가 용이

이 명세표를 바탕으로 각 파이프라인을 구현하면, 사용자는 명확한 Input을 제공하고 예측 가능한 Output을 받을 수 있습니다. 