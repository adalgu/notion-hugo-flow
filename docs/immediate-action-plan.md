# 즉시 실행 권장사항

## 🔍 현재 상황 요약

로그 분석 결과, **과거 캐시 문제가 아닌 Shortcode 호환성 문제**가 주요 원인입니다:

- ✅ 증분 처리 정상 작동 (변경사항 없어서 0개 처리)
- ✅ 155개 포스트 존재, 169개 페이지로 빌드 성공
- ⚠️ 18개 파일이 shortcode 문제로 임시 제외됨
- ⚠️ `{{< adsense >}}`, `{{< tweet >}}`, `{{< staticref >}}` 등이 Hugo에서 미지원

## 🚀 즉시 실행 권장 순서

### 옵션 A: 전체 강제 재빌드 (캐시 문제 완전 배제)

```bash
# 실행 권한 부여
chmod +x scripts/force-full-rebuild.sh

# 전체 강제 재빌드 실행
./scripts/force-full-rebuild.sh
```

### 옵션 B: Shortcode 문제 해결 후 점진적 처리

```bash
# 1. Shortcode 문제 해결
chmod +x scripts/fix-shortcodes.sh
./scripts/fix-shortcodes.sh

# 2. 변경사항 커밋
git add .
git commit -m "Fix shortcode compatibility issues

- Replace unsupported shortcodes with Hugo-compatible alternatives
- Convert adsense shortcodes to comments
- Convert tweet shortcodes to twitter shortcodes
- Convert staticref shortcodes to comments for manual review"
git push
```

### 권장사항: 옵션 A 먼저 시도

전체 강제 재빌드(`--full-sync`)를 통해 캐시 문제를 완전히 배제하고, 
실제 문제가 shortcode인지 캐시인지 명확히 파악할 수 있습니다.

### 3단계: GitHub Actions 실행 확인

- GitHub에서 Actions 탭 확인
- 빌드 로그에서 "9개의 문제 파일이 발견되었습니다" 메시지가 사라지는지 확인

### 4단계: 결과 검증

- 웹사이트 접속하여 포스트들이 정상적으로 표시되는지 확인
- 이전에 제외되었던 포스트들이 다시 나타나는지 확인

## 🔧 추가 최적화 (선택사항)

### GitHub Actions 워크플로우 개선

현재 `.github/workflows/` 파일에 다음 단계 추가:

```yaml
- name: Validate shortcodes
  run: |
    echo "=== Shortcode 검증 ==="
    ADSENSE_COUNT=$(grep -r "{{< adsense >}}" content/posts/ | wc -l)
    TWEET_COUNT=$(grep -r "{{< tweet " content/posts/ | wc -l)
    STATICREF_COUNT=$(grep -r "{{< staticref " content/posts/ | wc -l)
    
    echo "문제가 있는 shortcode 수:"
    echo "- adsense: $ADSENSE_COUNT"
    echo "- tweet: $TWEET_COUNT"
    echo "- staticref: $STATICREF_COUNT"
    
    if [ $((ADSENSE_COUNT + TWEET_COUNT + STATICREF_COUNT)) -gt 0 ]; then
      echo "⚠️ 호환되지 않는 shortcode가 발견되었습니다."
      exit 1
    fi
```

### 정기적 정리 작업

```yaml
- name: Weekly cleanup
  if: github.event_name == 'schedule'
  run: |
    # error_temp 디렉토리 정리
    find data/error_temp -name "*.md" -mtime +7 -delete 2>/dev/null || true
    
    # 빈 디렉토리 정리
    find data -type d -empty -delete 2>/dev/null || true
```

## 📊 예상 결과

이 작업 후 예상되는 변화:

1. **빌드 시간 단축**: 문제 파일 임시 이동/복원 과정 제거
2. **안정성 향상**: shortcode 오류로 인한 빌드 실패 위험 제거
3. **포스트 정상 표시**: 이전에 제외되었던 포스트들이 정상적으로 표시
4. **로그 정리**: "9개의 문제 파일" 메시지 제거

## 🎯 핵심 포인트

**과거 캐시 문제가 아닌 shortcode 호환성 문제**였습니다:

- 증분 처리는 정상 작동 중
- 실제 문제는 Hugo에서 지원하지 않는 shortcode 사용
- 해결책: shortcode를 Hugo 호환 형태로 변경

이 방법으로 "과거 포스트 지속 노출" 문제를 근본적으로 해결할 수 있습니다.
