# Database ID 보안 관리 가이드

## 🔒 문제 상황

기존 `notion-hugo.config.yaml` 파일에 database_id가 하드코딩되어 있어 다음과 같은 보안 문제가 있었습니다:

1. **Git 저장소 노출**: database_id가 공개 저장소에 노출됨
2. **원클릭 배포 제약**: 사용자가 수동으로 database_id를 설정해야 함
3. **보안 위험**: 민감한 정보가 코드에 포함됨

## ✅ 해결책: 하이브리드 접근 방식

**환경변수 우선 + YAML 폴백** 방식을 도입하여 보안과 편의성을 모두 확보했습니다.

### 1. 환경변수 우선 처리

```bash
# .env 파일
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID_POSTS=your_database_id_for_posts
```

### 2. YAML 폴백 지원

```yaml
# notion-hugo.config.yaml
mount:
  databases:
  - target_folder: posts
    # 환경변수가 없을 때만 사용됩니다
    # database_id: your_database_id_here
  manual: true
```

## 🚀 사용 방법

### 방법 1: 자동 설정 (권장)

```bash
# 개선된 설정 스크립트 사용
python setup_enhanced.py -i
```

이 방법은:
- ✅ 자동으로 database_id를 환경변수로 설정
- ✅ .gitignore에 .env 파일 자동 추가
- ✅ 배포 환경 자동 설정

### 방법 2: 수동 설정

1. **환경변수 설정**
   ```bash
   # .env 파일 생성
   echo "NOTION_TOKEN=your_token" > .env
   echo "NOTION_DATABASE_ID_POSTS=your_db_id" >> .env
   ```

2. **보안 설정**
   ```bash
   # .gitignore에 추가
   echo ".env" >> .gitignore
   ```

## 🔧 환경변수 명명 규칙

### 폴더명 기반 (권장)
```bash
NOTION_DATABASE_ID_POSTS=db_id_for_posts
NOTION_DATABASE_ID_DOCS=db_id_for_docs
NOTION_DATABASE_ID_NEWS=db_id_for_news
```

### 인덱스 기반 (여러 데이터베이스용)
```bash
NOTION_DATABASE_ID_0=first_database_id
NOTION_DATABASE_ID_1=second_database_id
NOTION_DATABASE_ID_2=third_database_id
```

## 🌐 배포 환경 설정

### Vercel 배포

1. **자동 설정** (setup_enhanced.py 사용)
   ```bash
   python setup_enhanced.py --token YOUR_TOKEN --deploy vercel
   ```

2. **수동 설정**
   - Vercel 대시보드 → Settings → Environment Variables
   - `NOTION_TOKEN` 추가
   - `NOTION_DATABASE_ID_POSTS` 추가

### GitHub Pages 배포

1. **자동 설정** (setup_enhanced.py 사용)
   ```bash
   python setup_enhanced.py --token YOUR_TOKEN --deploy github-pages
   ```

2. **수동 설정**
   - GitHub 저장소 → Settings → Secrets and variables → Actions
   - `NOTION_TOKEN` 추가
   - `NOTION_DATABASE_ID_POSTS` 추가

## 📋 우선순위 처리 로직

시스템은 다음 순서로 database_id를 찾습니다:

1. **환경변수 (폴더명 기반)**: `NOTION_DATABASE_ID_POSTS`
2. **환경변수 (인덱스 기반)**: `NOTION_DATABASE_ID_0`
3. **YAML 설정**: `database_id` 필드
4. **오류**: 모든 방법에서 찾지 못하면 오류 발생

## 🔍 코드 구현

### 개선된 config.py

```python
# 환경변수에서 ID 찾기 (폴더명 기반 -> 인덱스 기반 -> YAML 폴백)
database_id = (
    os.environ.get(f"NOTION_DATABASE_ID_{target_folder.upper()}")
    or os.environ.get(f"NOTION_DATABASE_ID_{i}")
    or db_config.get("database_id")
)
```

### 로깅 시스템

```python
# 환경변수 사용 여부 로깅
if os.environ.get(env_key):
    print(f"[Info] 환경변수 {env_key}에서 database_id 로드")
elif os.environ.get(env_key_indexed):
    print(f"[Info] 환경변수 {env_key_indexed}에서 database_id 로드")
else:
    print(f"[Info] YAML 설정에서 database_id 로드")
```

## 🛡️ 보안 모범 사례

### 1. 로컬 개발
- ✅ `.env` 파일 사용
- ✅ `.gitignore`에 `.env` 추가
- ❌ YAML에 database_id 직접 입력 금지

### 2. 배포 환경
- ✅ 플랫폼 환경변수 사용 (Vercel, GitHub Actions)
- ✅ 자동 설정 스크립트 활용
- ❌ 하드코딩된 값 사용 금지

### 3. 팀 협업
- ✅ `.env.sample` 파일로 템플릿 제공
- ✅ 문서화된 환경변수 목록
- ❌ 실제 값이 포함된 파일 공유 금지

## 📁 파일 구조

```
project/
├── .env                          # Git 제외, 로컬 환경변수
├── .env.sample                   # Git 포함, 템플릿
├── .gitignore                    # .env 제외 설정
├── notion-hugo.config.yaml       # 폴백 설정
├── setup_enhanced.py             # 자동 설정 스크립트
└── src/
    └── config.py                 # 개선된 설정 로더
```

## 🔄 마이그레이션 가이드

### 기존 사용자

1. **백업**
   ```bash
   cp notion-hugo.config.yaml notion-hugo.config.yaml.backup
   ```

2. **환경변수 추출**
   ```bash
   # 기존 YAML에서 database_id 확인
   grep database_id notion-hugo.config.yaml
   ```

3. **환경변수 설정**
   ```bash
   echo "NOTION_DATABASE_ID_POSTS=extracted_id" >> .env
   ```

4. **YAML 정리**
   ```yaml
   # database_id 라인을 주석 처리
   # database_id: extracted_id
   ```

### 새 사용자

```bash
# 자동 설정 사용 (권장)
python setup_enhanced.py -i
```

## 🎯 장점 요약

1. **보안 강화**: 민감한 정보가 Git에 노출되지 않음
2. **원클릭 배포**: 환경변수만 설정하면 자동 배포 가능
3. **하위 호환성**: 기존 YAML 설정도 계속 작동
4. **유연성**: 여러 데이터베이스 지원
5. **자동화**: 설정 스크립트로 완전 자동화

## 🆘 문제 해결

### Q: 환경변수가 로드되지 않아요
A: `.env` 파일이 프로젝트 루트에 있는지 확인하고, `python-dotenv`가 설치되어 있는지 확인하세요.

### Q: 배포 환경에서 database_id를 찾을 수 없어요
A: 배포 플랫폼의 환경변수 설정을 확인하세요. Vercel은 Environment Variables, GitHub Pages는 Secrets에서 설정합니다.

### Q: 여러 데이터베이스를 사용하고 싶어요
A: 폴더명 기반 환경변수를 사용하세요: `NOTION_DATABASE_ID_POSTS`, `NOTION_DATABASE_ID_DOCS` 등

이 가이드를 통해 database_id를 안전하고 편리하게 관리할 수 있습니다! 🚀
