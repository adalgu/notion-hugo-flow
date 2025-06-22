# GitHub Actions 워크플로우 Build/Deploy Job 분리 기록

**날짜:** 2025-06-22  
**작성자:** Cline (AI Assistant)  
**작업 경로:** `.github/workflows/notion-hugo-deploy.yml`

---

## 주요 변경 내용

- 기존의 단일 `build-and-deploy` job 구조를 **build**와 **deploy** 두 개의 job으로 분리
- `build` job: 빌드, 마크다운 변환, 아티팩트 업로드 등 모든 빌드 관련 작업 수행
- `deploy` job: `needs: build`로 빌드 완료 후 실행, GitHub Pages에 배포
- `deploy` job에 `environment`와 `url`을 명시하여 Actions UI에서 배포 환경 및 URL이 명확히 표기됨

---

## 변경 전 구조

```yaml
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      ...
      - name: Build with Hugo
      - name: Upload artifact
      - name: Deploy to GitHub Pages
```

## 변경 후 구조

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      ...
      - name: Build with Hugo
      - name: Upload artifact

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

---

## 기대 효과

- **빌드와 배포 단계의 명확한 분리**로 워크플로우 가독성 및 유지보수성 향상
- GitHub Actions UI에서 각 단계의 성공/실패를 별도 확인 가능
- 배포 환경(environment) 및 실제 배포 URL이 Actions 결과 화면에 명확히 표기됨
- 향후 배포 정책, 권한 관리, 조건부 배포 등 확장성 확보

---

## 커밋/적용 내역

- 커밋 메시지:  
  `refactor: split build and deploy jobs in GitHub Actions for clearer workflow`
- main 브랜치에 push 완료

---

## 참고

- `.github/workflows/notion-hugo-deploy.yml` 최신 상태를 기준으로 향후 워크플로우 수정 필요 시 반드시 이 구조를 참고할 것
- 추가 개선점이나 문제 발생 시 `docs/development_logs/`에 후속 기록을 남길 것
