# 동기화 모드 감지 문제 해결

## 🐛 발견된 문제

GitHub Actions에서 커밋 메시지를 제대로 감지하지 못하는 문제가 발생했습니다.

### 문제 상황
```
COMMIT_MSG=""  # 빈 문자열
```

## 🔧 적용된 해결책

### 1. 다중 방법으로 커밋 메시지 가져오기
```bash
# 1차: GitHub 이벤트에서 가져오기
COMMIT_MSG="${{ github.event.head_commit.message }}"

# 2차: Git 명령어로 직접 가져오기 (fallback)
if [[ -z "$COMMIT_MSG" ]]; then
  COMMIT_MSG="$(git log -1 --pretty=%B)"
fi
```

### 2. 디버그 정보 추가
```bash
echo "Debug info:"
echo "- Commit message: '$COMMIT_MSG'"
echo "- Ref name: '$REF_NAME'"
echo "- Event name: '$EVENT_NAME'"
```

### 3. 수동 실행 조건 추가
```bash
# workflow_dispatch (수동 실행)도 full-sync로 처리
[[ "$EVENT_NAME" == "workflow_dispatch" ]]
```

## 📋 테스트 방법

### 1. 커밋 메시지 테스트
```bash
git commit -m "Test commit with [full-sync] keyword"
git push origin main
```

### 2. 브랜치명 테스트
```bash
git checkout -b test/full-sync-branch
git push origin test/full-sync-branch
```

### 3. 수동 실행 테스트
- GitHub Actions → "Run workflow" 버튼 클릭

## 🔍 로그에서 확인할 내용

### 성공적인 감지
```
Debug info:
- Commit message: 'Test commit with [full-sync] keyword'
- Ref name: 'main'
- Event name: 'push'
🔄 Full sync mode activated
Final sync mode: full-sync
```

### 실패한 감지 (이전)
```
Debug info:
- Commit message: ''
- Ref name: 'main'
- Event name: 'push'
⚡ Incremental sync mode activated
Final sync mode: incremental
```

## 💡 추가 개선사항

### 1. 더 강력한 fallback 방법
만약 여전히 문제가 발생한다면:

```bash
# 3차: 최근 커밋들에서 검색
if [[ -z "$COMMIT_MSG" ]]; then
  COMMIT_MSG="$(git log -5 --pretty=%B | grep -E '\[(full-sync|force-rebuild)\]' | head -1)"
fi
```

### 2. 환경 변수 활용
```bash
# GitHub Actions secrets에 FORCE_FULL_SYNC=true 설정 시
if [[ "${{ secrets.FORCE_FULL_SYNC }}" == "true" ]]; then
  echo "mode=full-sync" >> $GITHUB_OUTPUT
  echo "🔄 Full sync mode activated (forced by secret)"
  exit 0
fi
```

## 🎯 권장 사용법

현재 수정된 버전에서는 다음과 같이 사용하세요:

### 확실한 full-sync 실행
1. **수동 실행**: GitHub Actions에서 "Run workflow" 버튼
2. **브랜치명**: `feature/full-sync-test` 같은 브랜치 생성
3. **커밋 메시지**: `[full-sync]` 또는 `[force-rebuild]` 포함

### 문제 발생 시 대안
```bash
# 임시로 브랜치명 활용
git checkout -b hotfix/full-sync-$(date +%Y%m%d)
git commit -m "Force full rebuild"
git push origin hotfix/full-sync-$(date +%Y%m%d)
```

이제 커밋 메시지 감지가 더 안정적으로 작동할 것입니다!
