#!/bin/bash

# 레거시 파일 정리 스크립트
# UUID 패턴의 파일들과 문제가 있는 파일들을 정리

echo "=== 레거시 파일 정리 시작 ==="

# 1. UUID 패턴 파일들 찾기 및 백업
echo "1. UUID 패턴 파일들 검색 중..."
UUID_FILES=$(find content/posts -name "1b87522e-*.md" -type f)

if [ ! -z "$UUID_FILES" ]; then
    echo "발견된 UUID 파일들:"
    echo "$UUID_FILES"
    
    # 백업 디렉토리 생성
    BACKUP_DIR="data/legacy_backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # UUID 파일들 백업 후 삭제
    echo "UUID 파일들을 백업 중..."
    for file in $UUID_FILES; do
        cp "$file" "$BACKUP_DIR/"
        rm "$file"
        echo "삭제됨: $file"
    done
    
    echo "백업 위치: $BACKUP_DIR"
else
    echo "UUID 패턴 파일이 없습니다."
fi

# 2. error_temp 디렉토리의 오래된 파일들 정리
echo "2. error_temp 디렉토리 정리 중..."
if [ -d "data/error_temp" ]; then
    # 7일 이상 된 파일들 삭제
    find data/error_temp -name "*.md" -mtime +7 -delete
    echo "7일 이상 된 임시 파일들을 삭제했습니다."
fi

# 3. 상태 파일 초기화 (선택적)
echo "3. 상태 파일 확인..."
if [ -f "src/config/.notion-hugo-state.json" ]; then
    echo "현재 상태 파일이 존재합니다. 필요시 수동으로 삭제하세요."
    echo "삭제 명령: rm src/config/.notion-hugo-state.json"
fi

echo "=== 레거시 파일 정리 완료 ==="
