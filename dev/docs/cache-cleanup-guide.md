# 캐시 및 과거 포스트 정리 가이드

## 문제 상황 분석

현재 로그 분석 결과:
1. **UUID 기반 레거시 파일들이 여전히 존재** (1b87522e-로 시작하는 파일들)
2. **Shortcode 문제로 18개 파일이 빌드에서 제외됨**
3. **증분 처리는 정상 작동하지만 삭제된 페이지 처리 부족**

## 즉시 실행 가능한 해결책

### 1. 레거시 파일 정리 (권장)

```bash
# 정리 스크립트 실행 권한 부여
chmod +x scripts/cleanup-legacy-files.sh

# 레거시 파일 정리 실행
./scripts/cleanup-legacy-files.sh
```

### 2. 캐시 완전 초기화

```bash
# 상태 파일 삭제 (전체 재빌드 강제)
rm src/config/.notion-hugo-state.json

# GitHub Actions 캐시 무효화를 위한 커밋
git add .
git commit -m "Force cache invalidation"
git push
```

### 3. 수동으로 문제 파일들 확인 및 삭제

```bash
# UUID 패턴 파일들 찾기
find content/posts -name "1b87522e-*.md" -type f

# 문제가 있는 shortcode 파일들 확인
grep -r "{{< adsense >}}" content/posts/
grep -r "{{< tweet " content/posts/
grep -r "{{< staticref " content/posts/
```

## GitHub Actions 워크플로우 개선 방안

### 1. 정기적 정리 작업 추가

현재 워크플로우에 다음 단계를 추가하는 것을 권장:

```yaml
- name: Clean up legacy files
  run: |
    # UUID 패턴 파일들 삭제
    find content/posts -name "1b87522e-*.md" -type f -delete
    
    # 7일 이상 된 error_temp 파일들 정리
    find data/error_temp -name "*.md" -mtime +7 -delete 2>/dev/null || true

- name: Force full rebuild on schedule
  if: github.event_name == 'schedule'
  run: |
    rm -f src/config/.notion-hugo-state.json
    echo "Forced full rebuild due to scheduled run"
```

### 2. 캐시 키 개선

```yaml
- name: Cache Notion state
  uses: actions/cache@v4
  with:
    path: src/config/.notion-hugo-state.json
    key: notion-state-${{ github.ref }}-${{ hashFiles('notion-hugo.config.yaml') }}
    restore-keys: |
      notion-state-${{ github.ref }}-
      notion-state-main-
```

## 근본적 해결 방안

### 1. Notion 데이터베이스 정리

- Notion에서 더 이상 필요하지 않은 페이지들을 완전히 삭제
- 페이지 상태를 "Published"에서 다른 상태로 변경

### 2. 파일명 규칙 개선

현재 `2025-03-17-` 접두사 방식이 좋습니다. UUID 기반 파일들은 모두 정리하는 것을 권장합니다.

### 3. Shortcode 문제 해결

문제가 되는 shortcode들을 Hugo에서 지원하는 형태로 변경하거나 제거:

```markdown
# 문제가 되는 형태
{{< adsense >}}
{{< tweet 1234567890 >}}
{{< staticref "path/to/file" >}}

# 대안
- adsense: HTML 직접 삽입 또는 partials 사용
- tweet: Hugo의 기본 twitter shortcode 사용
- staticref: 상대 경로 또는 Hugo의 ref/relref 사용
```

## 모니터링 및 예방

### 1. 정기적 점검

```bash
# 주간 점검 스크립트
echo "=== 주간 파일 점검 ==="
echo "UUID 패턴 파일 수: $(find content/posts -name "1b87522e-*.md" | wc -l)"
echo "Error temp 파일 수: $(find data/error_temp -name "*.md" 2>/dev/null | wc -l)"
echo "총 포스트 수: $(find content/posts -name "*.md" | wc -l)"
```

### 2. 알림 설정

GitHub Actions에서 문제 발생 시 Slack 등으로 알림을 받도록 설정

## 권장 실행 순서

1. **즉시 실행**: `./scripts/cleanup-legacy-files.sh`
2. **상태 파일 삭제**: `rm .notion-hugo-state.json`
3. **커밋 및 푸시**: 변경사항을 GitHub에 반영
4. **GitHub Actions 실행 확인**: 새로운 빌드가 정상적으로 실행되는지 확인
5. **결과 검증**: 웹사이트에서 과거 포스트들이 제거되었는지 확인

이 방법들을 통해 과거 캐시 문제와 레거시 파일 문제를 해결할 수 있습니다.
