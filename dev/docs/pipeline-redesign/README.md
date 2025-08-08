# 파이프라인 재설계 문서

## 📋 개요

이 폴더는 Notion-Hugo 파이프라인의 완전한 재설계 작업에 대한 문서들을 포함합니다. 기존의 복잡하고 혼란스러운 구조를 5개의 독립적인 파이프라인으로 분리하여 유지보수성과 확장성을 크게 향상시켰습니다.

## 📚 문서 읽기 순서

### 1. [NEW_PIPELINE_ARCHITECTURE.md](./NEW_PIPELINE_ARCHITECTURE.md)
**새로운 파이프라인 아키텍처 설계**
- 기존 문제점 분석
- 새로운 5개 파이프라인 구조
- 핵심 설계 원칙
- 마이그레이션 계획

### 2. [PIPELINE_SPECIFICATIONS.md](./PIPELINE_SPECIFICATIONS.md)
**Input/Output 명세표**
- 각 파이프라인의 상세한 Input/Output 정의
- 사용 시나리오별 매핑
- 파이프라인 간 데이터 전달 방식
- 명령어 및 워크플로우

### 3. [ADVANCED_SCENARIOS.md](./ADVANCED_SCENARIOS.md)
**고급 사용 시나리오**
- 백업/복구 파이프라인
- LLM 통합 파이프라인
- Notion 의존성 리스크 완화
- 통합 워크플로우 시나리오

### 4. [PIPELINE_REDESIGN_HANDOFF.md](./PIPELINE_REDESIGN_HANDOFF.md)
**핸드오프 문서**
- 완료된 작업 요약
- 현재 상태
- 다음 단계 및 구현 계획
- 참조 파일 목록

## 🎯 핵심 개선사항

### 기존 문제점
- 2467줄의 거대한 `app.py` 파일
- 복잡한 사용자 시나리오 (4가지)
- 설정 파일 중복 및 혼란
- 유지보수 어려움

### 새로운 구조
```
NOTION PIPELINE → HUGO PIPELINE → DEPLOYMENT PIPELINE
BACKUP PIPELINE ← → LLM PIPELINE
```

### 핵심 장점
1. **명확한 책임 분리**: 각 파이프라인이 하나의 명확한 목적
2. **독립적 실행**: 필요한 파이프라인만 선택적 실행
3. **쉬운 디버깅**: 문제가 발생한 파이프라인만 집중 분석
4. **확장성**: 새로운 플랫폼이나 기능 추가 용이
5. **유지보수성**: 코드 구조가 단순하고 명확

## 🚀 구현 계획

### Phase 1: 핵심 파이프라인 구현 (우선순위: 높음)
1. Notion Pipeline 완성
2. Hugo Pipeline 구현
3. Deployment Pipeline 구현

### Phase 2: 고급 파이프라인 구현 (우선순위: 중간)
4. Backup Pipeline 구현
5. LLM Pipeline 구현

### Phase 3: 통합 및 마이그레이션 (우선순위: 낮음)
6. 통합 파이프라인 구현
7. 기존 코드 마이그레이션
8. 테스트 및 검증

## 📁 관련 파일 구조

```
src/
├── notion/          # Notion 파이프라인
├── hugo/            # Hugo 파이프라인
├── deployment/      # 배포 파이프라인
├── backup/          # 백업 파이프라인
└── llm/             # LLM 파이프라인

drafts/
├── llm-generated/   # LLM 생성 콘텐츠
├── manual/          # 수동 작성 콘텐츠
└── approved/        # 승인된 콘텐츠

backup/
├── content/         # 로컬 백업
├── remote/          # 원격 백업
└── cloud/           # 클라우드 백업
```

## 🔗 관련 링크

- [기존 복잡한 app.py](../src/app.py) (참고용)
- [기존 설정 파일](../src/config/notion-hugo-config.yaml.clean) (참고용)
- [기존 사용자 시나리오](../USER_SCENARIOS_AND_FLOW.md) (참고용)

---

**이 재설계를 통해 프로젝트의 복잡함을 완전히 해결하고, 각 단계가 명확한 Input/Output을 가진 독립적인 파이프라인으로 작동하게 됩니다.** 