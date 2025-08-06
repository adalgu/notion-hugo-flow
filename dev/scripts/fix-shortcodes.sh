#!/bin/bash

# Shortcode 문제 해결 스크립트
echo "=== Shortcode 문제 해결 시작 ==="

# 백업 디렉토리 생성
BACKUP_DIR="data/shortcode_backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. adsense shortcode 제거 (또는 HTML로 대체)
echo "1. adsense shortcode 처리 중..."
find content/posts -name "*.md" -type f -exec grep -l "{{< adsense >}}" {} \; | while read file; do
    echo "처리 중: $file"
    cp "$file" "$BACKUP_DIR/"
    # adsense shortcode를 주석으로 변경
    sed -i 's/{{< adsense >}}/<!-- adsense placeholder -->/g' "$file"
done

# 2. tweet shortcode를 Hugo 기본 twitter shortcode로 변경
echo "2. tweet shortcode 처리 중..."
find content/posts -name "*.md" -type f -exec grep -l "{{< tweet " {} \; | while read file; do
    echo "처리 중: $file"
    if [ ! -f "$BACKUP_DIR/$(basename "$file")" ]; then
        cp "$file" "$BACKUP_DIR/"
    fi
    # tweet shortcode를 twitter shortcode로 변경
    sed -i 's/{{< tweet \([0-9]*\) >}}/{{< twitter \1 >}}/g' "$file"
done

# 3. staticref shortcode 제거 또는 일반 링크로 변경
echo "3. staticref shortcode 처리 중..."
find content/posts -name "*.md" -type f -exec grep -l "{{< staticref " {} \; | while read file; do
    echo "처리 중: $file"
    if [ ! -f "$BACKUP_DIR/$(basename "$file")" ]; then
        cp "$file" "$BACKUP_DIR/"
    fi
    # staticref를 주석으로 변경 (수동 검토 필요)
    sed -i 's/{{< staticref \([^>]*\) >}}/<!-- staticref: \1 -->/g' "$file"
done

echo "백업 위치: $BACKUP_DIR"
echo "=== Shortcode 문제 해결 완료 ==="

# 처리된 파일 수 확인
echo "=== 처리 결과 ==="
echo "adsense 남은 파일: $(grep -r "{{< adsense >}}" content/posts/ | wc -l)"
echo "tweet 남은 파일: $(grep -r "{{< tweet " content/posts/ | wc -l)"
echo "staticref 남은 파일: $(grep -r "{{< staticref " content/posts/ | wc -l)"
