#!/bin/bash

# 전체 강제 재빌드 스크립트
# 캐시 문제를 완전히 배제하고 모든 페이지를 다시 처리

echo "=== 전체 강제 재빌드 시작 ==="

# 1. 현재 상태 백업
echo "1. 현재 상태 백업 중..."
BACKUP_DIR="data/full_rebuild_backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "src/config/.notion-hugo-state.json" ]; then
    cp "src/config/.notion-hugo-state.json" "$BACKUP_DIR/"
    echo "상태 파일 백업됨: $BACKUP_DIR/.notion-hugo-state.json"
fi

# 2. 캐시 및 상태 파일 완전 삭제
echo "2. 캐시 및 상태 파일 삭제 중..."
rm -f src/config/.notion-hugo-state.json
echo "상태 파일 삭제됨"

# 3. 임시 파일들 정리
echo "3. 임시 파일들 정리 중..."
if [ -d "data/error_temp" ]; then
    rm -rf data/error_temp/*
    echo "error_temp 디렉토리 정리됨"
fi

# 4. Hugo 캐시 정리 (있다면)
echo "4. Hugo 캐시 정리 중..."
if [ -d "resources" ]; then
    rm -rf resources/_gen
    echo "Hugo 리소스 캐시 정리됨"
fi

# 5. 전체 강제 동기화 실행
echo "5. 전체 강제 동기화 실행 중..."
echo "명령어: python notion_hugo_app.py --full-sync --verbose"

python notion_hugo_app.py --full-sync --verbose

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ 전체 강제 재빌드 성공!"
    
    # 결과 요약
    echo ""
    echo "=== 재빌드 결과 요약 ==="
    echo "총 포스트 수: $(find content/posts -name "*.md" | wc -l)"
    echo "상태 파일 생성됨: $([ -f "src/config/.notion-hugo-state.json" ] && echo "Yes" || echo "No")"
    
    # Hugo 빌드 테스트
    echo ""
    echo "6. Hugo 빌드 테스트 중..."
    hugo --quiet
    BUILD_RESULT=$?
    
    if [ $BUILD_RESULT -eq 0 ]; then
        echo "✅ Hugo 빌드 성공!"
        echo "빌드된 페이지 수: $(find public -name "*.html" | wc -l)"
    else
        echo "❌ Hugo 빌드 실패"
    fi
    
else
    echo "❌ 전체 강제 재빌드 실패 (종료 코드: $RESULT)"
    echo "백업 위치: $BACKUP_DIR"
fi

echo ""
echo "=== 전체 강제 재빌드 완료 ==="
