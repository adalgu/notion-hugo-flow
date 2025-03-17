# GitHub Actions 워크플로우 권한 오류 해결

- **날짜**: 2025-03-17
- **작성자**: Notion-Hugo 개발팀
- **관련 이슈**: GitHub Actions 권한 오류
- **이전 로그**: [GitHub Pages 자동화 구현](./2025-03-17-integration-github-pages-automation.md)

## 문제 상황

Notion to Hugo Sync 워크플로우 실행 중 GitHub Actions 봇이 저장소에 변경사항을 푸시할 수 없는 권한 오류가 발생했습니다:

```
remote: Permission to adalgu/adalgu.github.io.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/adalgu/adalgu.github.io/': The requested URL returned error: 403
Error: Process completed with exit code 128.
```

이 오류는 GitHub Actions가 저장소에 쓰기 작업을 수행할 수 있는 적절한 권한이 없을 때 발생합니다. 워크플로우가 Notion에서 콘텐츠를 가져와 성공적으로 마크다운으로 변환한 후, 이 변경사항을 커밋하고 푸시하려고 할 때 권한 부족으로 인해 실패하게 됩니다.

## 해결 전략

GitHub Actions 워크플로우에는 세 가지 권한 설정 방법이 있습니다:

1. 저장소 설정에서 전역적으로 워크플로우 권한 설정
2. 워크플로우 파일에 직접 권한 설정 추가
3. 개인 액세스 토큰(PAT) 사용

이 중에서 두 번째 방법인 워크플로우 파일에 직접 권한을 설정하는 접근 방식을 선택했습니다. 이 방법은 다음과 같은 이점이 있습니다:

- 설정이 코드로 관리되어 버전 관리 가능
- 특정 워크플로우에만 권한을 부여할 수 있어 최소 권한 원칙 준수
- 저장소 설정을 변경하지 않고도 문제 해결 가능

## 구현 세부사항

`.github/workflows/notion-sync.yml` 파일에 다음과 같이 권한 설정을 추가했습니다:

```yaml
name: Notion to Hugo Sync

on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다 실행 (필요에 따라 조정 가능)
  workflow_dispatch:  # 수동 트리거 허용

# 저장소 권한 설정 추가
permissions:
  contents: write  # 저장소 콘텐츠에 대한 쓰기 권한

jobs:
  sync:
    runs-on: ubuntu-latest
    # 나머지 워크플로우 내용...
```

`permissions` 블록을 워크플로우 파일의 `on` 섹션과 `jobs` 섹션 사이에 추가했습니다. `contents: write` 설정은 GitHub Actions 워크플로우가 저장소 콘텐츠를 수정하고 변경사항을 푸시할 수 있는 권한을 부여합니다.

## 기술적 고려사항

### GitHub Actions 권한 모델

GitHub Actions의 권한 모델은 기본적으로 "최소 권한 원칙"을 따릅니다. 즉, 워크플로우는 명시적으로 필요한 권한만 가져야 한다는 원칙입니다. 권한은 다음 수준에서 설정할 수 있습니다:

1. **조직 수준**: 조직의 모든 저장소에 적용
2. **저장소 수준**: 특정 저장소의 모든 워크플로우에 적용
3. **워크플로우 수준**: 특정 워크플로우 파일에만 적용

워크플로우 수준에서 설정된 권한은 저장소 수준에서 설정된 권한보다 우선합니다.

### 권한 종류

GitHub Actions에서 사용할 수 있는 주요 권한 종류는 다음과 같습니다:

- `contents`: 저장소 콘텐츠에 대한 액세스
- `packages`: 패키지 관리
- `issues`: 이슈 관리
- `pull-requests`: PR 관리
- `pages`: GitHub Pages 설정
- `id-token`: OIDC 토큰 요청

각 권한은 `read`, `write`, `none` 수준으로 설정할 수 있습니다.

### Hugo 워크플로우 권한

참고로, Hugo 빌드 및 배포를 담당하는 `.github/workflows/hugo.yml` 파일에는 이미 다음과 같은 권한 설정이 있습니다:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

이 설정은 GitHub Pages 배포를 위한 것으로, `contents`에 대해서는 읽기 권한만 부여되어 있지만 `pages`와 `id-token`에 대해서는 쓰기 권한이 필요합니다. 이는 Pages 배포 작업의 특성을 반영한 것입니다.

## 다음 단계

이 해결 방법을 통해 GitHub Actions 워크플로우가 성공적으로 Notion 콘텐츠를 동기화하고 변경사항을 저장소에 푸시할 수 있게 되었습니다. 향후 다음과 같은 개선을 고려할 수 있습니다:

1. 커밋 메시지 형식 개선 및 일관성 유지
2. 워크플로우 실행 결과 알림 설정 (이메일, Slack 등)
3. 오류 발생 시 자동 재시도 메커니즘 구현
4. 워크플로우 실행 로그 분석 및 모니터링 도구 통합

## 참고 자료

- [GitHub Actions 권한 설정 문서](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [GitHub Actions 보안 강화 가이드](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [GitHub Actions 워크플로우 문법](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)
