# GitHub Actions 워크플로우 변경 로그

## 변경 내용 (2025-06-22)

### 목적
과거 포스트 지속 노출 문제 해결을 위해 incremental 처리에서 전체 강제 처리로 임시 변경

### 변경 사항
```diff
- python notion_hugo_app.py --incremental --state-file $STATE_FILE
+ python notion_hugo_app.py --full-sync --state-file $STATE_FILE
```

### 기대 효과
1. **캐시 문제 완전 배제**: 모든 페이지를 강제로 다시 처리
2. **삭제된 페이지 정리**: Notion에서 삭제된 페이지들이 Hugo에서도 제거됨
3. **문제 원인 명확화**: incremental vs full-sync 차이로 실제 원인 파악

### 모니터링 포인트
- [ ] 빌드 시간 증가 (예상: 2-3배)
- [ ] "9개의 문제 파일" 메시지 변화
- [ ] 과거 포스트 노출 문제 해결 여부
- [ ] 전체 포스트 수 변화

### 다음 단계
1. **워크플로우 실행**: 수동 트리거 또는 다음 스케줄 실행 대기
2. **결과 분석**: 로그 확인 및 웹사이트 검증
3. **원인 파악**: 문제가 해결되면 incremental 문제, 지속되면 shortcode 문제
4. **최적화**: 문제 해결 후 incremental로 복원 또는 shortcode 수정

### 롤백 방법
문제 발생 시 다음 명령으로 롤백:
```bash
# .github/workflows/notion-hugo-deploy.yml 파일에서
python notion_hugo_app.py --incremental --state-file $STATE_FILE
```

### 참고 파일
- `scripts/force-full-rebuild.sh` - 로컬 테스트용
- `scripts/fix-shortcodes.sh` - shortcode 문제 해결용
- `docs/immediate-action-plan.md` - 종합 해결 가이드
