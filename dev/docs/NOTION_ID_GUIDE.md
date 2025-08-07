# Notion ID 가이드: Database ID vs Page ID

## 🔍 개요

Notion에서 Database ID와 Page ID는 형식적으로는 동일하지만, 개념적으로는 다른 용도로 사용됩니다. 이 문서는 두 ID의 관계와 올바른 사용법을 설명합니다.

## 📋 ID 형식

### 공통 형식
- **32자리 16진수 UUID**: `8a021de7-2bda-434d-b255-d7cc94ebb567`
- **하이픈 포함**: `8a021de7-2bda-434d-b255-d7cc94ebb567`
- **하이픈 제외**: `8a021de72bda434db255d7cc94ebb567`

## 🎯 Database ID vs Page ID

### Database ID
- **정의**: Database 블록이 포함된 페이지의 고유 식별자
- **특징**: 
  - Database 블록이 포함된 페이지의 Page ID와 동일
  - `/databases/{database_id}` API 엔드포인트 사용
  - 테이블 형태의 데이터 구조
- **용도**: 블로그 포스트, 문서 목록 등 구조화된 데이터

### Page ID
- **정의**: 일반적인 페이지의 고유 식별자
- **특징**:
  - 모든 Notion 페이지의 기본 식별자
  - `/pages/{page_id}` API 엔드포인트 사용
  - 자유로운 콘텐츠 구조
- **용도**: About 페이지, 개별 문서 등

## 🔗 관계 설명

```
Notion Workspace
├── 일반 페이지 (Page ID만 존재)
│   └── ID: 8a021de7-2bda-434d-b255-d7cc94ebb567
│
└── Database 페이지 (Page ID = Database ID)
    ├── Page ID: 8a021de7-2bda-434d-b255-d7cc94ebb567
    ├── Database ID: 8a021de7-2bda-434d-b255-d7cc94ebb567 (동일!)
    └── Database 블록 포함
```

## 💡 핵심 포인트

1. **Database는 특별한 Page**: Database는 Database 블록이 포함된 특별한 페이지입니다.
2. **동일한 ID**: Database의 Page ID와 Database ID는 항상 동일합니다.
3. **API 차이**: 같은 ID라도 다른 API 엔드포인트를 사용합니다.

## 🏷️ 환경 변수 명명 규칙

### 권장 명명 패턴

```bash
# Database ID (Database 블록이 포함된 페이지)
NOTION_DATABASE_ID_POSTS=8a021de7-2bda-434d-b255-d7cc94ebb567
NOTION_DATABASE_ID_DOCS=9b132ef8-3ceb-545e-c366-e8dd05fcc678

# Page ID (일반 페이지)
NOTION_PAGE_ID_ABOUT=7c243fg9-4dfc-656f-d477-f9ee16gdd789
NOTION_PAGE_ID_CONTACT=6d354gh0-5egd-767g-e588-g0ff17hee890
```

### 명명 규칙

1. **Database ID**: `NOTION_DATABASE_ID_{용도}`
   - 예: `NOTION_DATABASE_ID_POSTS`, `NOTION_DATABASE_ID_DOCS`

2. **Page ID**: `NOTION_PAGE_ID_{용도}`
   - 예: `NOTION_PAGE_ID_ABOUT`, `NOTION_PAGE_ID_CONTACT`

## 🔧 코드에서의 사용

### 현재 구현
```python
def is_notion_database_id(id_str: str) -> bool:
    """현재 구현에서는 페이지 ID와 데이터베이스 ID의 형식이 동일합니다."""
    return is_notion_page_id(id_str)
```

### 올바른 사용법
```python
# Database ID 사용 (테이블 데이터)
database_id = os.environ.get("NOTION_DATABASE_ID_POSTS")
notion.databases.query(database_id=database_id)

# Page ID 사용 (일반 페이지)
page_id = os.environ.get("NOTION_PAGE_ID_ABOUT")
notion.pages.retrieve(page_id=page_id)
```

## ⚠️ 주의사항

1. **혼동 방지**: Database ID와 Page ID는 형식이 같지만 용도가 다릅니다.
2. **명확한 명명**: 환경 변수 이름으로 용도를 명확히 구분하세요.
3. **API 선택**: 올바른 API 엔드포인트를 사용하세요.

## 📝 예시

### 올바른 설정
```yaml
# src/config/notion-hugo-config.yaml
notion:
  mount:
    databases:
      - database_id: "${NOTION_DATABASE_ID_POSTS:-}"  # Database 블록 페이지
        target_folder: "posts"
    pages:
      - page_id: "${NOTION_PAGE_ID_ABOUT:-}"  # 일반 페이지
        target_file: "pages/about.md"
```

### 환경 변수
```bash
# .env
NOTION_DATABASE_ID_POSTS=8a021de7-2bda-434d-b255-d7cc94ebb567
NOTION_PAGE_ID_ABOUT=7c243fg9-4dfc-656f-d477-f9ee16gdd789
```

## 🔍 ID 확인 방법

1. **Notion URL에서 추출**:
   ```
   https://notion.so/myworkspace/8a021de7-2bda-434d-b255-d7cc94ebb567
   ↑ ID: 8a021de7-2bda-434d-b255-d7cc94ebb567
   ```

2. **API로 확인**:
   ```python
   # Database인지 확인
   try:
       notion.databases.retrieve(database_id=id)
       print("✅ Database ID")
   except:
       print("❌ Not a Database ID")
   ``` 