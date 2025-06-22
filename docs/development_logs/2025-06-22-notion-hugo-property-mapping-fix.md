# 2025-06-22 Notion-Hugo Property Mapping Fix & 현황

## 주요 이슈 및 해결 과정

### 1. 문제 배경
- Notion-Hugo 파이프라인에서 `isPublished`와 `skipRendering` 체크박스 속성에 따라 포스트의 발행/비발행, 렌더링/비렌더링이 제대로 동작하지 않는 현상 발견.
- 특히, Notion에서 속성명이 소문자(`ispublished`, `skiprendering`)로 내려오는데 기존 파이프라인은 대소문자 구분(`isPublished`, `skipRendering`)으로 처리하여 항상 기본값(`draft=true`)이 적용되는 문제.

### 2. 주요 증상
- `isPublished`와 `skipRendering` 모두 체크가 안된(즉, false) 포스트가 발행(draft: false)되는 현상.
- 예시: 페이지 ID `20e7522eeb2f80ef9700d6ffe9b5473b`가 Notion에서 두 속성이 모두 false임에도 Hugo에서 발행됨.

### 3. 해결 과정
- `src/property_mapper.py`에서 대소문자 구분 없이 속성명을 찾도록 로직 개선.
  - `process_publication_status()`에서 `isPublished` 속성을 `.lower()`로 비교하여 찾음.
  - `should_skip_page()`에서도 `skipRendering`/`doNotRendering`을 대소문자 구분 없이 처리.
- `isPublished=false`일 때 반드시 `draft=true`가 되도록 보장.
- 디버깅 로그로 실제 변환 결과 및 속성 흐름을 추적하여 문제 재현 및 검증.
- 코드 정리 및 디버깅 로그 제거.

### 4. 남은 문제 및 추가 확인 필요 사항
- 여전히 `isPublished=false`이고 `skipRendering=false`인 경우, Hugo에서 `draft: true`로 생성되어야 함.
- 특정 페이지(예: `20e7522eeb2f80ef9700d6ffe9b5473b`)가 실제로 `draft: false`로 생성되는지 추가 검증 필요.
- Notion API에서 해당 페이지의 실제 속성값을 직접 확인하여, 파이프라인에서 올바르게 읽고 있는지 점검 필요.

### 5. 커밋 및 배포
- 관련 코드(`src/property_mapper.py`, `src/render.py`) 및 문서(README, troubleshooting-guide) 수정 후 커밋 및 푸시 완료.
- 커밋 해시: f92e439

### 6. 향후 액션 플랜
- 문제 페이지의 실제 프론트매터(`draft`) 값과 Notion 원본 속성값을 비교하여 최종 검증.
- 필요시 테스트 케이스 추가 및 예외 상황 로깅 강화.
- 향후 속성명 변경/추가에 대비해 모든 속성 처리에서 대소문자 구분 없는 접근 유지.

---

**작성일:** 2025-06-22  
**작성자:** Cline (AI)
