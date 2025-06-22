# [2025-06-22] URL 리디렉션 및 SEO 최적화 시스템 구축

## 문제 상황
- Hugo 블로그의 포스트 URL 정책이 `/post/슬러그` → `/posts/슬러그`로 변경됨
- 과거 검색엔진에 인덱싱된 `/post/슬러그`, `/posts/2025-03-17-슬러그` 등 다양한 패턴의 URL이 404로 연결되는 문제 발생
- 404 에러는 SEO에 부정적 영향을 미치고, 사용자 경험도 저하됨

## 개선 및 적용 내역

### 1. 서버 레벨 리디렉션
- **Netlify/Vercel**: `static/_redirects` 파일에 패턴별 301 리디렉션 규칙 추가
- **Apache/Nginx**: `static/.htaccess` 파일에 동일한 리디렉션 규칙 추가

### 2. 클라이언트 사이드 리디렉션
- `layouts/partials/redirect.html` : /post/*, /archives 등 주요 패턴 JS 리디렉션
- `layouts/partials/smart-redirect.html` : 404 상황에서 슬러그 패턴 추정 및 자동 이동

### 3. 404 페이지 개선
- `layouts/404.html` : 404 발생 시 유사 URL 자동 탐색 및 안내, 2초 후 자동 이동

### 4. robots.txt 및 sitemap
- `static/robots.txt` : 구 URL 패턴 크롤링 차단, sitemap 위치 명시

## 기대 효과
- 과거 검색엔진에 인덱싱된 모든 URL이 새 URL로 자동 리디렉션 (301)
- SEO 점수 및 링크 주스 보존
- 사용자 경험 개선, 404 발생률 감소
- 검색엔진 크롤러가 더 빠르게 새 URL 구조로 인식

## 주요 커밋 메시지
- Restore archives.md file for date-based page listing
- Add URL redirection system: /post/* to /posts/* and /archives to /posts/
- Add comprehensive SEO-friendly redirect system for old slug patterns

## 참고
- 적용 파일: `_redirects`, `.htaccess`, `redirect.html`, `smart-redirect.html`, `404.html`, `robots.txt`
- 향후 URL 정책 변경 시에도 위 구조를 참고하여 리디렉션 규칙 추가 필요
