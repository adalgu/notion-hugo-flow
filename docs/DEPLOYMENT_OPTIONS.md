# 배포 옵션 가이드

Notion-Hugo 블로그를 배포하는 두 가지 주요 방법을 설명합니다.

## 🚀 빠른 비교

| 항목 | Vercel | GitHub Pages |
|------|--------|-------------|
| **설정 복잡도** | ⭐ (매우 쉬움) | ⭐⭐ (쉬움) |
| **배포 속도** | ⭐⭐⭐ (매우 빠름) | ⭐⭐ (빠름) |
| **무료 한도** | 100GB 대역폭/월 | 무제한 |
| **커스텀 도메인** | ⭐⭐⭐ (매우 쉬움) | ⭐⭐ (가능) |
| **HTTPS** | 자동 | 자동 |
| **전역 CDN** | ⭐⭐⭐ | ⭐⭐ |
| **빌드 시간** | 제한 없음 | 10분 제한 |

## 1. Vercel 배포 (추천)

### 장점
- 설정이 가장 간단 (클릭 몇 번)
- 매우 빠른 전역 CDN
- 자동 HTTPS 및 커스텀 도메인 설정
- 실시간 배포 미리보기
- 뛰어난 성능 최적화

### 단점
- 무료 플랜 대역폭 제한 (월 100GB)
- 상업적 사용 시 유료 플랜 필요

### 🚀 Vercel 원클릭 배포

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fadalgu%2Fnotion-hugo-py&env=NOTION_TOKEN&envDescription=Notion%20API%20Token&envLink=https%3A%2F%2Fdevelopers.notion.com%2Fdocs%2Fcreate-a-notion-integration)

**설정 과정:**
1. 위 버튼 클릭
2. GitHub에서 저장소 Fork
3. Notion API 토큰 입력
4. 배포 완료!

### 수동 Vercel 설정

```bash
# 1. Vercel CLI 설치
npm i -g vercel

# 2. 프로젝트 클론 및 설정
git clone https://github.com/adalgu/notion-hugo-py.git
cd notion-hugo-py

# 3. Notion 설정
python notion_hugo_app.py -i

# 4. Vercel 배포
vercel --prod
```

## 2. GitHub Pages 배포

### 장점
- 완전 무료 (대역폭 제한 없음)
- GitHub 생태계와 완벽 통합
- 소스코드와 배포가 한 곳에서 관리
- 안정적이고 신뢰할 수 있음

### 단점
- 초기 설정이 약간 복잡
- Vercel보다 느린 배포 속도
- 빌드 시간 10분 제한

### 🚀 GitHub Pages 원클릭 설정

```bash
# 1. 저장소 클론
git clone https://github.com/adalgu/notion-hugo-py.git
cd notion-hugo-py

# 2. 노션 API 키를 .env 파일에 저장
echo "NOTION_TOKEN=your_notion_token_here" > .env

# 3. 원클릭 GitHub Pages 설정
./scripts/github-pages-setup.sh
```

이 스크립트가 자동으로 처리하는 작업:
- GitHub 저장소 생성 (없는 경우)
- GitHub Pages 활성화
- Notion API 토큰을 GitHub Secrets에 등록
- 워크플로우 파일 설정
- 첫 번째 배포 실행

### GitHub Actions 워크플로우

자동으로 생성되는 워크플로우 파일 `.github/workflows/notion-hugo-deploy.yml`:

```yaml
name: Notion → Hugo → GitHub Pages

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */2 * * *'  # 2시간마다 자동 동기화
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

env:
  HUGO_VERSION: 0.128.0

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        run: |
          wget -O ${{ runner.temp }}/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${{ env.HUGO_VERSION }}/hugo_extended_${{ env.HUGO_VERSION }}_linux-amd64.deb
          sudo dpkg -i ${{ runner.temp }}/hugo.deb

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install notion-client python-dotenv pyyaml fs tabulate

      - name: Run Notion sync
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
        run: |
          python notion_hugo_app.py --incremental

      - name: Build with Hugo
        run: hugo --minify

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## 3. 커스텀 도메인 설정

### Vercel에서 커스텀 도메인

1. Vercel 대시보드에서 프로젝트 선택
2. Settings → Domains
3. 도메인 추가 및 DNS 설정 따라하기

### GitHub Pages에서 커스텀 도메인

1. 저장소 Settings → Pages
2. Custom domain에 도메인 입력
3. DNS에서 CNAME 레코드 설정:
   ```
   www.yourdomain.com → yourusername.github.io
   ```

## 4. 환경변수 및 시크릿 설정

### Vercel 환경변수

Vercel 대시보드에서:
1. 프로젝트 → Settings → Environment Variables
2. `NOTION_TOKEN` 추가

### GitHub Secrets

GitHub 저장소에서:
1. Settings → Secrets and variables → Actions
2. `NOTION_TOKEN` 시크릿 추가

## 5. 문제 해결

### Vercel 배포 실패

**증상**: 빌드 실패 또는 404 오류
**해결책**:
1. 빌드 로그 확인
2. `vercel.json` 설정 검증
3. 환경변수 확인

### GitHub Pages 배포 실패

**증상**: Actions 실패 또는 사이트 접근 불가
**해결책**:
1. Actions 탭에서 로그 확인
2. Pages 설정에서 Source가 "GitHub Actions"로 설정되었는지 확인
3. Secrets에 `NOTION_TOKEN`이 올바르게 설정되었는지 확인

### 공통 문제

**노션 동기화 실패**
- Notion API 토큰 권한 확인
- 통합이 데이터베이스와 공유되었는지 확인
- 데이터베이스 ID가 올바른지 확인

**Hugo 빌드 실패**
- Hugo 버전 호환성 확인
- 테마 설정 확인
- 마크다운 문법 오류 확인

## 6. 성능 최적화

### Vercel 최적화

```json
// vercel.json
{
  "build": {
    "env": {
      "HUGO_VERSION": "0.140.0",
      "HUGO_ENV": "production",
      "HUGO_EXTENDED": "true"
    }
  },
  "buildCommand": "python notion_hugo_app.py && hugo --gc --minify",
  "outputDirectory": "public",
  "framework": "hugo",
  "functions": {
    "app/**/*.py": {
      "runtime": "python3.9"
    }
  }
}
```

### GitHub Pages 최적화

- 증분 동기화 활용 (`--incremental`)
- 캐시 활용으로 빌드 시간 단축
- 스마트 동기화로 불필요한 빌드 방지

## 7. 모니터링 및 분석

### Vercel Analytics

- 자동 성능 모니터링
- 실시간 방문자 통계
- Core Web Vitals 추적

### GitHub Pages + Google Analytics

```html
<!-- layouts/partials/extend_head.html -->
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_TRACKING_ID');
</script>
```

## 8. 백업 및 복구

### 자동 백업 전략

1. **소스 백업**: GitHub 저장소가 자동 백업 역할
2. **콘텐츠 백업**: Notion이 원본 데이터 저장소
3. **빌드 아티팩트**: 배포 플랫폼에서 자동 보관

### 복구 절차

1. 새 환경에서 저장소 클론
2. 환경변수/시크릿 재설정
3. 배포 플랫폼 연결
4. 첫 빌드 실행

이제 두 배포 옵션 모두 원클릭으로 설정할 수 있으며, 사용자의 필요에 따라 선택할 수 있습니다.
