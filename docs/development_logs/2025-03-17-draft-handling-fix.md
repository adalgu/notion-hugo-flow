# Draft Handling Fix

**Date**: 2025-03-17
**Author**: Notion-Hugo Team

## Issue

GitHub Pages 사이트에 포스트가 표시되지 않는 문제가 발생했습니다. 조사 결과, 노션에서 변환된 모든 포스트가 `draft: true` 상태로 설정되어 있었으며, Hugo는 기본적으로 초안 상태의 콘텐츠를 빌드하지 않습니다.

## 해결 방법

다음과 같은 접근 방식을 검토했습니다:

1. `draft: false`를 기본값으로 설정
2. Hugo 빌드 시 `--buildDrafts` 플래그 추가
3. 노션 데이터베이스에서 `isPublished` 속성을 명시적으로 설정

안전성과 편의성을 고려하여 두 번째 옵션을 선택했습니다. 이렇게 하면 기본적으로 모든 포스트가 초안 상태로 유지되어 실수로 비공개 콘텐츠가 노출될 위험을 줄이면서도, `--buildDrafts` 플래그를 통해 모든 콘텐츠가 웹사이트에 표시됩니다.

## 변경 사항

1. `.github/workflows/hugo.yml` 파일에 `--buildDrafts` 플래그를 추가했습니다:
```yaml
hugo \
  --minify \
  --buildDrafts \
  --baseURL "${{ steps.pages.outputs.base_url }}/"
```

2. `scripts/github-pages-setup.sh` 스크립트를 업데이트하여 `buildDrafts` 옵션에 대한 설명을 추가했습니다.

3. 향후 참조를 위해 `docs/draft-handling-guide.md` 문서를 작성했습니다. 이 문서는 초안 관리 방식과 다양한 옵션을 설명합니다.

## 테스트 결과

적용된 변경 사항을 테스트한 결과, 모든 노션 포스트가 GitHub Pages 사이트에 정상적으로 표시되었습니다.

## 추가 고려 사항

1. 향후 `isPublished` 속성을 노션 데이터베이스에 추가하여 더 세밀한 제어가 가능합니다.
2. 프로덕션 환경에서는 상황에 따라 `--buildDrafts` 플래그 사용 여부를 조정할 수 있습니다.
