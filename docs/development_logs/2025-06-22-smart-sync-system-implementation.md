# 스마트 동기화 시스템 구현 및 문제 해결 도구 개발

**날짜**: 2025-06-22  
**작업자**: AI Assistant (Cline)  
**작업 유형**: 기능 개발, 문제 해결, 시스템 개선  

## 📋 작업 개요

Notion-Hugo 파이프라인에서 **과거 포스트 지속 노출 문제**를 해결하기 위해 스마트 동기화 시스템을 구현하고, 다양한 문제 해결 도구를 개발했습니다.

## 🎯 해결한 주요 문제

### 1. 과거 포스트 지속 노출 문제
- **문제**: incremental 처리 과정에서 과거 캐시와의 문제로 인해 과거 포스트가 지속적으로 노출
- **원인 분석**: Shortcode 호환성 문제가 주요 원인으로 판명 (캐시 문제가 아님)
- **해결**: 스마트 동기화 시스템과 shortcode 수정 도구 개발

### 2. GitHub Actions 커밋 메시지 감지 문제
- **문제**: `${{ github.event.head_commit.message }}`가 빈 문자열로 전달됨
- **해결**: 다중 fallback 방법 구현 (`git log -1 --pretty=%B` 추가)

## 🧠 구현된 스마트 동기화 시스템

### 핵심 기능
1. **자동 모드 선택**: 커밋 메시지나 브랜치명에 따라 `incremental` 또는 `full-sync` 모드 자동 선택
2. **키워드 기반 제어**: `[full-sync]`, `[force-rebuild]` 키워드로 전체 재빌드 트리거
3. **브랜치 기반 제어**: 브랜치명에 `full-sync` 포함 시 자동으로 전체 동기화
4. **스케줄 최적화**: 정기 실행 시 자동으로 full-sync로 전체 정리

### 구현 파일
- **`.github/workflows/notion-hugo-deploy.yml`**: 스마트 모드 감지 로직 구현

```yaml
- name: Determine sync mode
  id: sync-mode
  run: |
    # 여러 방법으로 커밋 메시지 가져오기 시도
    COMMIT_MSG="${{ github.event.head_commit.message }}"
    if [[ -z "$COMMIT_MSG" ]]; then
      COMMIT_MSG="$(git log -1 --pretty=%B)"
    fi
    REF_NAME="${{ github.ref_name }}"
    EVENT_NAME="${{ github.event_name }}"
    
    echo "Debug info:"
    echo "- Commit message: '$COMMIT_MSG'"
    echo "- Ref name: '$REF_NAME'"
    echo "- Event name: '$EVENT_NAME'"
    
    # full-sync 조건들
    if [[ "$COMMIT_MSG" == *"[full-sync]"* ]] || \
       [[ "$COMMIT_MSG" == *"[force-rebuild]"* ]] || \
       [[ "$REF_NAME" == *"full-sync"* ]] || \
       [[ "$EVENT_NAME" == "schedule" ]] || \
       [[ "$EVENT_NAME" == "workflow_dispatch" ]]; then
      echo "mode=full-sync" >> $GITHUB_OUTPUT
      echo "🔄 Full sync mode activated"
    else
      echo "mode=incremental" >> $GITHUB_OUTPUT
      echo "⚡ Incremental sync mode activated"
    fi
```

## 🛠️ 개발된 문제 해결 도구

### 1. Shortcode 호환성 수정 도구
**파일**: `scripts/fix-shortcodes.sh`

```bash
#!/bin/bash
# Hugo에서 지원하지 않는 shortcode 자동 변환
# - adsense shortcode를 주석으로 변경
# - tweet shortcode를 twitter shortcode로 변경
# - staticref shortcode를 주석으로 변경
```

### 2. 전체 강제 재빌드 도구
**파일**: `scripts/force-full-rebuild.sh`

```bash
#!/bin/bash
# 캐시 문제를 완전히 배제하고 모든 페이지를 다시 처리
# - 상태 파일 완전 삭제
# - 모든 캐시 정리
# - --full-sync 옵션으로 전체 페이지 강제 처리
```

### 3. 레거시 파일 정리 도구
**파일**: `scripts/cleanup-legacy-files.sh`

```bash
#!/bin/bash
# UUID 패턴의 파일들과 문제가 있는 파일들을 정리
# - UUID 패턴 파일들 백업 후 삭제
# - error_temp 디렉토리의 오래된 파일들 정리
```

## 📚 생성된 문서

### 1. 사용법 가이드
- **`docs/smart-sync-usage-guide.md`**: 스마트 동기화 상세 사용법
- **`docs/troubleshooting-sync-mode.md`**: 동기화 모드 문제 해결
- **`docs/immediate-action-plan.md`**: 즉시 실행 가이드
- **`docs/cache-cleanup-guide.md`**: 캐시 정리 종합 가이드
- **`docs/workflow-change-log.md`**: GitHub Actions 워크플로우 변경 로그

### 2. README.md 업데이트
새로운 스마트 동기화 시스템과 문제 해결 도구들을 README.md에 추가:

```markdown
## 🧠 스마트 동기화 사용법

### 커밋 메시지로 모드 제어
# 전체 재빌드 (캐시 문제 해결)
git commit -m "Fix cache issues [full-sync]"
git push origin main

### 브랜치명으로 모드 제어
git checkout -b hotfix/full-sync-cache-fix
git push origin hotfix/full-sync-cache-fix

## 🛠️ 문제 해결 도구
# Shortcode 호환성 문제
chmod +x scripts/fix-shortcodes.sh
./scripts/fix-shortcodes.sh
```

## 🔍 문제 분석 결과

### 실제 원인: Shortcode 호환성 문제
로그 분석 결과, 과거 포스트 지속 노출 문제의 실제 원인은:
- **18개 파일**이 `{{< adsense >}}`, `{{< tweet >}}`, `{{< staticref >}}` shortcode 문제로 빌드에서 임시 제외됨
- 이 파일들이 임시로 `data/error_temp/`로 이동 후 복원되는 방식으로 처리됨
- 증분 처리는 정상 작동하지만, shortcode 문제로 인한 파일 제외가 주요 원인

### 해결 효과
1. **빌드 시간 단축**: 문제 파일 임시 이동/복원 과정 제거
2. **안정성 향상**: shortcode 오류로 인한 빌드 실패 위험 제거
3. **포스트 정상 표시**: 이전에 제외되었던 포스트들이 정상적으로 표시
4. **로그 정리**: "9개의 문제 파일" 메시지 제거

## 🎯 사용 시나리오

### 일반적인 사용 (자동 incremental)
```bash
git commit -m "Add new blog post"
git push origin main
# → 자동으로 incremental 모드 선택
```

### 캐시 문제 해결
```bash
git commit -m "Clear cache and rebuild all posts [full-sync]"
git push origin main
# → 자동으로 full-sync 모드 선택
```

### 브랜치를 통한 제어
```bash
git checkout -b hotfix/full-sync-needed
git push origin hotfix/full-sync-needed
# → 자동으로 full-sync 모드 선택
```

### 수동 실행
- GitHub Actions에서 "Run workflow" 버튼 클릭 시 자동으로 full-sync 모드

## 📊 기술적 세부사항

### 모드 감지 로직
1. **커밋 메시지 확인**: `[full-sync]`, `[force-rebuild]` 키워드 검색
2. **브랜치명 확인**: `full-sync` 문자열 포함 여부
3. **이벤트 타입 확인**: `schedule`, `workflow_dispatch` 시 자동 full-sync
4. **Fallback 처리**: GitHub 이벤트에서 커밋 메시지를 가져올 수 없을 때 Git 명령어 사용

### 디버그 정보
워크플로우 실행 시 다음 정보를 로그에 출력:
```
Debug info:
- Commit message: 'Your actual commit message [full-sync]'
- Ref name: 'main'
- Event name: 'push'
🔄 Full sync mode activated
Final sync mode: full-sync
```

## 🚀 다음 단계

### 확인된 추가 문제
사용자 피드백에 따르면 **`isPublished`와 `skipRendering` 체크박스 속성에 따른 포스트 처리가 제대로 수행되지 않는** 문제가 있음.

### 관련 파일
- **`src/property_mapper.py`**: 노션 속성과 Hugo 프론트매터 간의 매핑 처리

### 예정 작업
1. `property_mapper.py`의 `should_skip_page()` 메서드 검증
2. `process_publication_status()` 메서드의 `isPublished` → `draft` 변환 로직 확인
3. 메인 파이프라인에서 속성 처리 과정 디버깅

## 📈 성과 요약

1. **스마트 동기화 시스템**: 상황에 맞는 최적의 동기화 방식 자동 선택
2. **문제 해결 도구**: 일반적인 문제들에 대한 자동화된 해결책 제공
3. **사용자 경험 개선**: 간단한 키워드로 복잡한 시스템 제어 가능
4. **문서화**: 상세한 사용법과 문제 해결 가이드 제공
5. **안정성 향상**: 다양한 시나리오에 대한 견고한 처리 로직 구현

이번 작업으로 Notion-Hugo 파이프라인의 안정성과 사용성이 크게 향상되었으며, 사용자가 상황에 맞게 효율적으로 시스템을 운영할 수 있게 되었습니다.
