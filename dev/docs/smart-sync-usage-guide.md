# 스마트 동기화 사용 가이드

## 🎯 개요

GitHub Actions 워크플로우가 커밋 메시지나 브랜치명에 따라 자동으로 `incremental` 또는 `full-sync` 모드를 선택하도록 개선되었습니다.

## 🔄 Full-Sync 모드 트리거 방법

다음 조건 중 하나라도 만족하면 **full-sync** 모드로 실행됩니다:

### 1. 커밋 메시지에 키워드 포함
```bash
git commit -m "Fix shortcode issues [full-sync]"
git commit -m "Major content update [force-rebuild]"
```

### 2. 브랜치명에 키워드 포함
```bash
git checkout -b feature/full-sync-test
git checkout -b hotfix/full-sync-cache-fix
```

### 3. 스케줄 실행
- 매시간 자동 실행 시 항상 full-sync 모드

### 4. 수동 트리거
- GitHub Actions에서 "Run workflow" 버튼으로 실행 시

## ⚡ Incremental 모드 (기본값)

위 조건에 해당하지 않는 모든 경우에는 **incremental** 모드로 실행됩니다:

```bash
git commit -m "Update blog post content"
git commit -m "Fix typo in article"
git push origin main
```

## 📋 사용 예시

### 예시 1: 캐시 문제 해결이 필요한 경우
```bash
git add .
git commit -m "Clear cache and rebuild all posts [full-sync]"
git push origin main
```

### 예시 2: 대규모 컨텐츠 변경 후
```bash
git add .
git commit -m "Migrate all posts from old format [force-rebuild]"
git push origin main
```

### 예시 3: 일반적인 포스트 업데이트
```bash
git add .
git commit -m "Add new blog post about AI trends"
git push origin main
# → incremental 모드로 실행됨
```

### 예시 4: 브랜치를 통한 제어
```bash
git checkout -b hotfix/full-sync-needed
git add .
git commit -m "Fix critical issue"
git push origin hotfix/full-sync-needed
# → full-sync 모드로 실행됨
```

## 🔍 실행 모드 확인 방법

GitHub Actions 로그에서 다음과 같은 메시지로 확인할 수 있습니다:

### Full-Sync 모드
```
🔄 Full sync mode activated
🔄 Executing full synchronization...
```

### Incremental 모드
```
⚡ Incremental sync mode activated
⚡ Executing incremental synchronization...
```

## 📊 모드별 특징 비교

| 특징 | Incremental | Full-Sync |
|------|-------------|-----------|
| **실행 시간** | 빠름 (1-2분) | 느림 (5-10분) |
| **처리 범위** | 변경된 페이지만 | 모든 페이지 |
| **캐시 활용** | 기존 캐시 사용 | 캐시 무시 |
| **삭제된 페이지** | 감지 제한적 | 완전 정리 |
| **권장 사용** | 일반적인 업데이트 | 문제 해결, 대규모 변경 |

## 🛠️ 문제 해결

### 과거 포스트가 계속 나타나는 경우
```bash
git commit -m "Force rebuild to clear old posts [full-sync]"
```

### Shortcode 문제 해결 후
```bash
git commit -m "Fix shortcode compatibility [force-rebuild]"
```

### 정기적인 전체 정리
- 스케줄 실행(매시간)이 자동으로 full-sync를 수행하므로 별도 작업 불필요

## 💡 팁

1. **일반적인 경우**: 키워드 없이 커밋하여 빠른 incremental 모드 활용
2. **문제 발생 시**: `[full-sync]` 또는 `[force-rebuild]` 키워드 사용
3. **테스트 목적**: `full-sync`가 포함된 브랜치명 사용
4. **응급 상황**: GitHub Actions에서 수동 실행

이제 상황에 맞게 효율적으로 동기화 모드를 선택할 수 있습니다!
