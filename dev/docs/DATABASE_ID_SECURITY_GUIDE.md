# Database ID 보안 및 사용 가이드

## 🔍 개요

이 문서는 Notion-Hugo Flow에서 Database ID를 안전하고 효율적으로 관리하는 방법을 설명합니다.

## 🚀 CLI에서 Database ID 사용

### 1. **자동 생성 (기본)**
```bash
python app.py setup --token YOUR_NOTION_TOKEN
# → Database 자동 생성 + ID 자동 설정
```

### 2. **기존 Database ID 사용**
```bash
python app.py setup --token YOUR_NOTION_TOKEN --database-id EXISTING_DB_ID
# → 기존 Database ID를 사용하여 설정
```

### 3. **Database 마이그레이션**
```bash
python app.py setup --token YOUR_NOTION_TOKEN --migrate-from OLD_DB_ID
# → 기존 Database에서 새 Database로 마이그레이션
```

### 4. **인터랙티브 모드**
```bash
python app.py setup --token YOUR_NOTION_TOKEN --interactive
# → 대화형으로 Database 설정
```

## 🔐 핵심 보안 원칙

**"토큰만 있어도 Notion → Hugo → GitHub Pages가 가능하다"**

### ✅ **자동화된 보안**
- Database ID 자동 생성 및 설정
- 환경 변수 자동 관리
- 설정 파일 자동 업데이트
- `.gitignore` 자동 설정

### 🎯 **사용자 편의성**
- **최소 입력**: 토큰만 제공하면 모든 것이 자동 설정
- **유연성**: 기존 Database ID도 직접 지정 가능
- **안전성**: 민감한 정보는 환경 변수로 관리

## 📋 Database ID 관리 방법

### 1. **환경 변수 기반 (권장)**
```bash
# .env 파일
NOTION_DATABASE_ID_POSTS=8a021de7-2bda-434d-b255-d7cc94ebb567
```

### 2. **CLI 인자 기반**
```bash
# 직접 Database ID 지정
python app.py setup --token YOUR_TOKEN --database-id YOUR_DB_ID
```

### 3. **설정 파일 기반**
```yaml
# src/config/notion-hugo-config.yaml
notion:
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS:-}"
        target_folder: "posts"
```

## 🔧 Database ID 추출 방법

### 1. **Notion URL에서 추출**
```
https://notion.so/myworkspace/8a021de7-2bda-434d-b255-d7cc94ebb567
↑ Database ID: 8a021de7-2bda-434d-b255-d7cc94ebb567
```

### 2. **자동 추출 스크립트**
```bash
# Database ID 자동 추출
python -c "
from src.cli_utils import extract_notion_id_from_url
url = input('Notion URL: ')
id = extract_notion_id_from_url(url)
print(f'Database ID: {id}')
"
```

### 3. **환경 변수 설정**
```bash
# Database ID를 환경 변수로 설정
echo "NOTION_DATABASE_ID_POSTS=extracted_id" >> .env
```

## 🛡️ 보안 모범 사례

### 1. **환경 변수 사용**
```bash
# ✅ 권장: 환경 변수 사용
NOTION_DATABASE_ID_POSTS=your_db_id

# ❌ 피해야 할 것: 코드에 하드코딩
database_id = "8a021de7-2bda-434d-b255-d7cc94ebb567"
```

### 2. **Git 무시 설정**
```bash
# .gitignore에 추가
.env
.env.local
.env.production
```

### 3. **CI/CD 보안**
```yaml
# GitHub Actions에서 시크릿 사용
env:
  NOTION_DATABASE_ID_POSTS: ${{ secrets.NOTION_DATABASE_ID_POSTS }}
```

## 🔄 Database ID 변경 시나리오

### 1. **새 Database 생성**
```bash
# 기존 설정 유지하면서 새 Database 생성
python app.py setup --token YOUR_TOKEN
# → 새 Database 자동 생성 및 설정
```

### 2. **기존 Database 사용**
```bash
# 기존 Database ID 지정
python app.py setup --token YOUR_TOKEN --database-id EXISTING_ID
# → 기존 Database 사용
```

### 3. **Database 마이그레이션**
```bash
# 기존 Database에서 새 Database로 마이그레이션
python app.py setup --token YOUR_TOKEN --migrate-from OLD_ID
# → 데이터 마이그레이션 후 새 Database 사용
```

## 📊 Database ID 검증

### 1. **CLI 검증**
```bash
# Database ID 유효성 검사
python app.py validate
```

### 2. **수동 검증**
```python
from notion_client import Client

notion = Client(auth="your_token")
try:
    database = notion.databases.retrieve(database_id="your_db_id")
    print("✅ Database ID is valid")
except Exception as e:
    print(f"❌ Database ID is invalid: {e}")
```

## 🎯 요약

### **핵심 원칙**
1. **토큰만으로 시작**: `python app.py setup --token YOUR_TOKEN`
2. **자동화된 보안**: Database ID 자동 생성 및 관리
3. **유연한 옵션**: 기존 Database ID도 직접 지정 가능
4. **환경 변수 우선**: 민감한 정보는 환경 변수로 관리

### **사용 시나리오**
- **신규 사용자**: 토큰만 제공 → 모든 것이 자동 설정
- **기존 Database 사용자**: `--database-id` 옵션으로 기존 Database 사용
- **마이그레이션**: `--migrate-from` 옵션으로 데이터 이전

이제 **토큰만 있어도 Notion → Hugo → GitHub Pages**가 완전히 자동화되었습니다! 🚀
