# 🚀 Notion-Hugo: 노션을 블로그로, 3분 안에 완성

> **노션 API 키만 있으면 나머지는 자동화됩니다!**

노션에서 글 쓰고 → 체크박스 클릭 → 자동으로 블로그 배포 ✨

### 🏆 프로덕션 검증된 엔터프라이즈급 기능
- **스마트 속성 매핑**: Notion Properties ↔ Hugo Frontmatter 자동 변환
- **SEO 최적화**: 메타데이터, 키워드, 구조화된 데이터 자동 처리
- **증분 동기화**: 변경된 콘텐츠만 효율적으로 처리
- **고급 분류**: 카테고리, 태그, 키워드 체계적 관리

## ⚡ 3분 퀵 스타트

### 1️⃣ 원클릭 배포

#### Vercel로 배포 (추천)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/adalgu/adalgu.github.io)

1. 위 버튼 클릭 → GitHub 연결 → Vercel 배포
2. 환경변수 `NOTION_TOKEN` 설정 ([토큰 받기](https://notion.so/my-integrations))
3. 완료! 🎉

#### GitHub Pages로 배포
```bash
# 원클릭 자동 배포 (추천)
curl -sSL https://raw.githubusercontent.com/adalgu/adalgu.github.io/main/scripts/quick-deploy-github.sh | bash

# 또는 수동 다운로드 후 실행
wget https://raw.githubusercontent.com/adalgu/adalgu.github.io/main/scripts/quick-deploy-github.sh
chmod +x quick-deploy-github.sh
./quick-deploy-github.sh
```

### 2️⃣ 로컬에서 시작

```bash
# 1. 저장소 클론
git clone https://github.com/adalgu/adalgu.github.io.git
cd adalgu.github.io

# 2. 5분 설정 실행 (노션 키만 준비하세요!)
# 대화형 모드로 안전하게 설정
python app.py setup --interactive

# 또는 명령줄로 바로 실행
python app.py setup --token YOUR_NOTION_TOKEN
python app.py setup --token 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
# 3. 완료! 블로그가 생성됩니다
```

##  이게 전부예요!

1. **노션 API 키 발급** ([여기서 → ](https://notion.so/my-integrations))
2. **5분 설정 실행** (`python app.py setup --token YOUR_TOKEN`)
3. **노션에서 글쓰기** (체크박스만 체크하면 자동 발행!)

## 🎯 주요 특징

- ✅ **5분 설정**: 노션 키 → 스크립트 실행 → 완료
- ✅ **모던 CLI**: Click 기반의 직관적인 명령어 인터페이스
- ✅ **자동 동기화**: 노션 변경사항이 자동으로 블로그에 반영
- ✅ **원클릭 배포**: Vercel/GitHub Pages 즉시 배포
- ✅ **증분 업데이트**: 변경된 포스트만 빠르게 처리
- ✅ **SEO 최적화**: 메타태그, 리디렉션 자동 처리
- ✅ **스마트 매핑**: Notion Properties ↔ Hugo Frontmatter 자동 변환

## 🤔 FAQ

**Q: 어떤 노션 권한이 필요한가요?**
A: `Read content`, `Update content`, `Insert content` 권한만 있으면 됩니다.

**Q: 기존 노션 페이지도 사용할 수 있나요?**
A: 네! 설정 시 "기존 데이터베이스 마이그레이션" 선택하면 됩니다.

**Q: 글 발행은 어떻게 하나요?**
A: 노션에서 `isPublished` 체크박스만 체크하면 자동으로 블로그에 나타납니다.

**Q: 문제가 생기면 어떻게 하나요?**
A: [문제해결 가이드](docs/TROUBLESHOOTING.md)를 확인하세요.

**Q: 노션 속성과 Hugo 프론트매터는 어떻게 매핑되나요?**
A: [속성 매핑 분석](dev/docs/notion-hugo-property-mapping-analysis.md)에서 자세한 매핑 규칙을 확인하세요.

## 🎨 Notion-Hugo 속성 매핑 시스템

### 📋 2가지 구성 모드

#### 🚀 Mode 1: 최소 구성 (Minimal Setup)
**빠른 시작을 위한 필수 속성만**
```yaml
# Notion Database Properties
Name: title          # → Hugo: title
Date: date           # → Hugo: date  
isPublished: checkbox # → Hugo: draft (역의 관계)
Description: rich_text # → Hugo: description
Tags: multi_select   # → Hugo: tags
```

#### 🏆 Mode 2: 전문가 구성 (Professional Setup)
**포트폴리오급 SEO 최적화**
```yaml
# 필수 속성
Name, Date, isPublished

# SEO 최적화
Description, Summary, keywords, author, lastModified

# 고급 분류
categories, Tags, weight, slug

# 테마 지원
featured, subtitle, linkTitle, layout
```

### 🔧 고급 매핑 기능
- **Fallback 시스템**: `description` → `summary`, `tags` → `keywords`
- **역의 관계**: `isPublished: true` → `draft: false`
- **자동 처리**: 날짜, 슬러그, 대소문자 무관 처리
- **증분 동기화**: 변경된 페이지만 스마트 처리

> 📖 **[전체 매핑 분석 보기](dev/docs/notion-hugo-property-mapping-analysis.md)** - 15년차 Applied Scientist의 프로덕션 검증 모범 사례

## 📚 더 자세한 가이드

- **[상세 설정 가이드](docs/SETUP_GUIDE.md)** - 고급 설정과 커스터마이징
- **[배포 옵션 비교](docs/DEPLOYMENT_OPTIONS.md)** - Vercel vs GitHub Pages
- **[문제 해결](docs/TROUBLESHOOTING.md)** - 자주 묻는 질문과 해결책
- **[속성 매핑 분석](dev/docs/notion-hugo-property-mapping-analysis.md)** - Notion-Hugo 메타데이터 최적화

## 🛠️ CLI 사용법

```bash
# 5분 설정 (처음 사용 시)
python app.py setup --token YOUR_NOTION_TOKEN

# 노션에서 콘텐츠 동기화
python app.py sync                    # 변경사항만 (빠름)
python app.py sync --full             # 전체 동기화

# 휴고 사이트 빌드
python app.py build                   # 정적 사이트 생성
python app.py build --serve           # 로컬 서버 시작

# 전체 배포 파이프라인
python app.py deploy                  # 동기화 + 빌드 + 배포

# 설정 확인 및 문제 해결
python app.py validate               # 설정 검증
python app.py status                 # 현재 상태 확인
```

## 📄 라이선스

GPL-3.0 License

---

**🎉 이제 노션에서 글을 쓰고 체크박스만 클릭하세요. 나머지는 자동입니다!**
