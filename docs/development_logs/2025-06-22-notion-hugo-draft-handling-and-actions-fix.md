# 2025-06-22 Notion-Hugo Draft Handling & GitHub Actions Fix

## 주요 변경 및 개선 내역

### 1. Notion 속성 매핑 시스템 개선
- `isPublished`, `skipRendering` 속성 대소문자 구분 없이 인식하도록 PropertyMapper 개선
- `isPublished=false` → Hugo `draft=true` 변환 로직 정상화
- `skipRendering=true`인 경우 페이지 완전 건너뜀

### 2. GitHub Actions 워크플로우 수정
- `hugo --minify --buildDrafts ...` → `hugo --minify ...`로 변경
- 이제 프로덕션 빌드에서 draft 페이지가 사이트에 포함되지 않음
- 개발 서버/로컬에서는 필요시 `--buildDrafts`로 draft 확인 가능

### 3. Draft 페이지 처리 동작 검증
- content/posts 내 draft: true인 마크다운 파일은 그대로 존재
- Hugo 빌드 시(기본) draft 페이지는 public/에 생성되지 않음
- `--buildDrafts` 옵션을 주면 draft 페이지도 public/에 생성됨
- public/posts/ai-----browser-use---/ 등 draft 전용 디렉토리의 생성/제거 동작 확인

### 4. Incremental/Full-sync와의 관계
- **Incremental 모드**로도 draft 페이지 자동 정리됨(별도 full-sync 필요 없음)
- Hugo는 public 디렉토리를 매번 새로 생성하므로, draft 페이지가 자동으로 제외됨
- 과거에 draft로 처리된 페이지도 다음 빌드에서 자동으로 사라짐

### 5. 실제 검증 로그
- `find content/posts -name "*.md" -exec grep -l "draft: true" {} \;`로 draft 파일 확인
- `hugo --minify` 빌드 후 public/에 draft 디렉토리 미생성 확인
- `hugo --minify --buildDrafts` 빌드 후 public/에 draft 디렉토리 생성 확인

---

## 결론

- Notion-Hugo 파이프라인의 draft 처리 및 GitHub Actions 배포 동작이 명확하게 개선됨
- 프로덕션 사이트에 draft 페이지가 노출되는 문제 완전 해결
- 추가적인 full-sync 없이 incremental 모드만으로도 draft 페이지 자동 정리 가능

### 관련 커밋
- `be585b0 Fix: Remove --buildDrafts from GitHub Actions to prevent draft pages from being published`
