# Notion-Hugo Property Mapping Analysis

## 📋 개요

이 문서는 Notion 데이터베이스의 Properties와 Hugo Frontmatter 간의 매핑 시스템을 분석하고, 최적화된 블로그 메타데이터 구성을 제안합니다.

## 🔍 현재 매핑 시스템 분석

### 1. 핵심 매핑 아키텍처

현재 시스템은 `src/property_mapper.py`를 중심으로 다음과 같은 구조로 구성되어 있습니다:

```python
# 시스템 속성 (Notion API 자동 제공)
NOTION_SYSTEM_PROPERTIES = {
    "created_time": { "fallback_for": "date" },
    "last_edited_time": { "hugo_key": "lastmod" }
}

# 최소 필수 속성
MINIMAL_PROPERTIES = {
    "title": { "hugo_key": "title" },
    "date": { "hugo_key": "date" },
    "id": { "hugo_key": "notion_id" }
}

# 추천 속성 그룹
CONTENT_CONTROL_PROPERTIES = {...}
METADATA_PROPERTIES = {...}
TAXONOMY_PROPERTIES = {...}
THEME_PROPERTIES = {...}
```

### 2. 현재 지원하는 속성 매핑

#### 📝 최소 필수 속성 (Minimal Properties)
| Notion Property | Hugo Frontmatter | Type | Description |
|----------------|------------------|------|-------------|
| `Name` | `title` | title | 페이지 제목 |
| `Date` | `date` | date | 발행일 |
| `id` | `notion_id` | system | Notion 페이지 ID |

#### 🎛️ 콘텐츠 제어 속성 (Content Control)
| Notion Property | Hugo Frontmatter | Type | Description |
|----------------|------------------|------|-------------|
| `skipRendering` | - | checkbox | 페이지 처리 건너뛰기 |
| `isPublished` | `draft` | checkbox | 출판 상태 (역의 관계) |
| `expiryDate` | `expiryDate` | date | 만료일 |

#### 📊 메타데이터 속성 (Metadata)
| Notion Property | Hugo Frontmatter | Type | Description |
|----------------|------------------|------|-------------|
| `Description` | `description` | rich_text | 페이지 설명 (SEO) |
| `Summary` | `summary` | rich_text | 콘텐츠 요약 |
| `lastModified` | `lastmod` | date | 마지막 수정일 |
| `slug` | `slug` | rich_text | URL 경로 |
| `Author` | `author` | rich_text | 작성자 |
| `weight` | `weight` | number | 정렬 순서 |

#### 🏷️ 분류 속성 (Taxonomy)
| Notion Property | Hugo Frontmatter | Type | Description |
|----------------|------------------|------|-------------|
| `categories` | `categories` | multi_select | 카테고리 분류 |
| `Tags` | `tags` | multi_select | 태그 목록 |
| `keywords` | `keywords` | rich_text | SEO 키워드 |

#### 🎨 테마 지원 속성 (Theme Support)
| Notion Property | Hugo Frontmatter | Type | Description |
|----------------|------------------|------|-------------|
| `featured` | `featured` | checkbox | 특별 강조 게시물 |
| `subtitle` | `subtitle` | rich_text | 부제목 |
| `linkTitle` | `linkTitle` | rich_text | 링크 제목 |
| `layout` | `layout` | rich_text | 템플릿 레이아웃 |

## 🎯 최적화된 블로그 메타데이터 구성

### Mode 1: 최소 구성 (Minimal Setup)

**목적**: 빠른 시작과 간단한 관리
**대상**: 개인 블로그, 프로토타입, 간단한 콘텐츠 관리

#### 필수 속성만 포함:
```yaml
# Notion Database Properties
Name: title
Date: date
isPublished: checkbox
Description: rich_text
Tags: multi_select
```

#### Hugo Frontmatter 결과:
```yaml
---
title: "Your Post Title"
date: 2025-01-15T10:00:00Z
draft: false
description: "Post description for SEO"
tags: ["tag1", "tag2"]
notion_id: "page-id-here"
---
```

### Mode 2: 전문가 구성 (Professional Setup)

**목적**: SEO 최적화, 고급 콘텐츠 관리, 포트폴리오급 품질
**대상**: 기술 블로그, 포트폴리오, 기업 블로그

#### 완전한 속성 구성:
```yaml
# 필수 속성
Name: title
Date: date
isPublished: checkbox

# 콘텐츠 제어
skipRendering: checkbox
expiryDate: date

# 메타데이터 (SEO 최적화)
Description: rich_text
Summary: rich_text
lastModified: date
slug: rich_text
Author: rich_text
weight: number

# 분류 (고급 카테고리화)
categories: multi_select
Tags: multi_select
keywords: rich_text

# 테마 지원 (고급 표시)
featured: checkbox
subtitle: rich_text
linkTitle: rich_text
layout: rich_text
```

#### Hugo Frontmatter 결과:
```yaml
---
title: "Advanced Post Title"
date: 2025-01-15T10:00:00Z
lastmod: 2025-01-16T15:30:00Z
draft: false
description: "Comprehensive post description for SEO optimization"
summary: "Brief summary for preview cards"
author: "Your Name"
slug: "custom-url-slug"
weight: 1
categories: ["Technology", "Programming"]
tags: ["Python", "Machine Learning", "Tutorial"]
keywords: ["python, machine learning, tutorial, ai"]
featured: true
subtitle: "Advanced Subtitle"
linkTitle: "Short Title"
layout: "single"
notion_id: "page-id-here"
---
```

## 🔧 고급 매핑 기능

### 1. Fallback 시스템
```python
# description이 없으면 summary 사용
"summary": {
    "hugo_key": "summary",
    "fallback": "description"
}

# keywords가 없으면 tags 사용
"keywords": {
    "hugo_key": "keywords", 
    "fallback": "tags"
}
```

### 2. 역의 관계 처리
```python
# isPublished = true → draft = false
"isPublished": {
    "hugo_key": "draft",
    "inverse": True
}
```

### 3. 시스템 속성 자동 매핑
```python
# Notion API 자동 제공 속성
"created_time" → "date" (fallback)
"last_edited_time" → "lastmod" (fallback)
```

## 📈 SEO 최적화 권장사항

### 1. 필수 SEO 속성
- `description`: 메타 태그용 (150-160자 권장)
- `keywords`: 검색엔진 키워드
- `author`: 작성자 정보
- `lastmod`: 콘텐츠 최신성 표시

### 2. 고급 SEO 속성
- `featured`: 특별 콘텐츠 강조
- `weight`: 중요도 기반 정렬
- `categories`: 주제별 분류
- `tags`: 세부 키워드

### 3. URL 최적화
- `slug`: 커스텀 URL 경로
- 자동 슬러그 생성 (제목 기반)

## 🎨 테마별 지원 속성

### PaperMod 테마 (현재 사용)
- `featured`: 특별 게시물 강조
- `subtitle`: 부제목 표시
- `weight`: 메뉴 정렬
- `layout`: 커스텀 레이아웃

### 기타 인기 테마 지원
- **Ananke**: `featured`, `weight`
- **Congo**: `featured`, `subtitle`, `weight`
- **Stack**: `featured`, `weight`, `layout`

## 🔄 자동화 및 스마트 처리

### 1. 자동 날짜 처리
```python
# Date 속성이 없으면 created_time 사용
# lastModified가 없으면 last_edited_time 사용
```

### 2. 스마트 슬러그 생성
```python
# slug가 없으면 제목에서 자동 생성
# 특수문자 제거, 하이픈 변환
```

### 3. 대소문자 무관 처리
```python
# "Tags", "tags", "TAGS" 모두 동일 처리
# 사용자 실수 방지
```

## 🚀 성능 최적화

### 1. 증분 처리
- 변경된 페이지만 처리
- 상태 파일 기반 추적

### 2. 배치 처리
- 여러 페이지 동시 처리
- API 호출 최적화

### 3. 캐싱
- 메타데이터 캐싱
- 중복 처리 방지

## 📋 구현 체크리스트

### 최소 구성 체크리스트
- [ ] Name (title) 속성 설정
- [ ] Date 속성 설정
- [ ] isPublished 체크박스 설정
- [ ] Description 텍스트 필드 설정
- [ ] Tags 다중 선택 설정

### 전문가 구성 체크리스트
- [ ] 모든 필수 속성 설정
- [ ] SEO 최적화 속성 추가
- [ ] 고급 분류 속성 설정
- [ ] 테마 지원 속성 추가
- [ ] 자동화 설정 확인

## 🔮 향후 개선 방향

### 1. 고급 매핑 기능
- 조건부 매핑 (상황별 다른 처리)
- 동적 속성 생성
- 외부 API 연동

### 2. AI 기반 최적화
- 자동 태그 추천
- SEO 점수 분석
- 콘텐츠 품질 평가

### 3. 확장성 개선
- 플러그인 시스템
- 커스텀 매핑 규칙
- 다중 테마 지원

---
