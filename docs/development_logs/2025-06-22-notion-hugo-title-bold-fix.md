# Notion→Hugo 변환 파이프라인: 제목 볼드 마크다운(**) 자동 제거 개선

- **일시:** 2025-06-22
- **작성자:** Cline

## 문제 현상

- 노션에서 제목에 볼드 마크다운(**)이 포함된 경우, 휴고로 변환된 마크다운의 frontmatter title에도 **가 그대로 남아있어, 웹페이지 <h1> 태그에 **가 노출되는 문제가 발생함.
- 일부 포스트는 title에 **가 있고, 일부는 없음(입력 데이터 불일치).
- 예시: "**AI 기반 웹 자동화의 부상: Browser Use와 자동화 브라우징의 미래**" → 웹페이지에서 **가 그대로 표시됨

## 원인 분석

### 초기 분석 (잘못된 접근)
- 처음에는 `src/markdown_converter.py`의 `create_hugo_frontmatter` 함수에서 title 처리가 일어난다고 생각했음.
- 해당 함수에 볼드 마크다운 제거 코드를 추가했으나 효과가 없었음.

### 실제 원인 발견
- 실제로는 `src/render.py`의 `get_page_properties` 함수에서 title 추출이 일어남.
- `extract_rich_text` 함수가 노션의 rich_text에서 볼드 서식을 마크다운(**) 으로 변환하면서 문제 발생.
- `markdown_converter.py`의 함수는 실제로 사용되지 않는 코드였음.

## 해결 방법

### 1. 근본 원인 해결
- `src/render.py`의 `get_page_properties` 함수에서 title 추출 시 볼드 마크다운 제거 로직 추가:
  ```python
  if prop_type == "title":
      title_text = extract_rich_text(prop.get("title", []))
      # Remove markdown/HTML bold from title (for Notion->Hugo)
      import re
      title_text = re.sub(
          r"(\*\*|__|<b>|</b>|<strong>|</strong>)", "", title_text
      )
      properties["title"] = title_text
  ```

### 2. 기존 파일 일괄 처리
- `scripts/fix-title-bold-markdown.py` 스크립트 작성하여 기존 마크다운 파일들의 title에서 볼드 마크다운 제거.
- 25개 파일 검사 결과 3개 파일에서 볼드 마크다운 발견 및 제거:
  - `2024-02-12-fastapi에서의-디펜던시-인젝션dependency-injection.md`
  - `2024-02-22-elephantsql-postgresql과-python을-연동하는-방법-기초부터-코드-예제까지.md`
  - `2022-11-05-colab코랩에서-kogpt-실행.md`

## 기대 효과

- 휴고 렌더링 시 <h1> 태그에 **가 노출되는 문제 근본 해결.
- 향후 노션→휴고 변환 과정에서 title 볼드 표기 문제 재발 방지.
- 기존 마크다운 파일들의 일관성 확보.

## 교훈

- 문제 해결 시 실제 코드 실행 경로를 정확히 파악하는 것이 중요함.
- 사용되지 않는 코드와 실제 사용되는 코드를 구분해야 함.
- 근본 원인을 찾기 위해 전체 파이프라인의 데이터 흐름을 추적해야 함.

## 추가 분석: Incremental 모드와 기존 데이터 처리

- **질문**: `incremental` 처리 모드에서 기존에 **가 있던 포스트가 자동으로 수정되는가?
- **답변**: **아니요, 수정되지 않습니다.**
- **이유**:
  - `incremental` 모드는 노션의 `last_edited_time`을 비교하여 변경된 페이지만 처리합니다.
  - 기존 포스트의 노션 페이지가 실제로 수정되지 않았다면 `last_edited_time`이 동일하므로 건너뜁니다.
  - 따라서 우리가 수정한 `src/render.py`의 title 볼드 제거 로직이 적용되지 않습니다.
- **해결 방법**:
  - **--full-sync 옵션 사용**: `python -m src.notion_hugo --full-sync`
  - **메타데이터 파일 삭제**: `rm .notion-hugo-state.json`
  - **이번 사례에서는 `scripts/fix-title-bold-markdown.py` 스크립트로 이미 일괄 처리 완료**

## 참고

- 수정된 파일: `src/render.py`
- 일괄 처리 스크립트: `scripts/fix-title-bold-markdown.py`
- 적용일: 2025-06-22
