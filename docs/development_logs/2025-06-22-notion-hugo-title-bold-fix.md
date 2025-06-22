# Notion→Hugo 변환 파이프라인: 제목 볼드 마크다운(**) 자동 제거 개선

- **일시:** 2025-06-22
- **작성자:** Cline

## 문제 현상

- 노션에서 제목에 볼드 마크다운(**)이 포함된 경우, 휴고로 변환된 마크다운의 frontmatter title에도 **가 그대로 남아있어, 웹페이지 <h1> 태그에 **가 노출되는 문제가 발생함.
- 일부 포스트는 title에 **가 있고, 일부는 없음(입력 데이터 불일치).

## 원인

- 노션→휴고 변환 파이프라인에서 title 값을 별도의 후처리 없이 frontmatter에 기록함.
- 노션에서 볼드로 입력된 제목이 그대로 마크다운 파일에 반영됨.

## 개선 내용

- `src/markdown_converter.py`의 `create_hugo_frontmatter` 함수에서 title 내 **를 자동으로 제거하도록 코드 수정.
  ```python
  title = properties.get("title", "Untitled")
  # Remove markdown bold from title (for Notion->Hugo)
  title = title.replace("**", "")
  frontmatter.append(f'title: "{title}"')
  ```
- 이 변경으로 노션에서 볼드 마크다운이 포함된 제목도 휴고 변환 시 일관적으로 **가 제거됨.

## 기대 효과

- 휴고 렌더링 시 <h1> 태그에 **가 노출되는 문제 근본 해결.
- 기존 마크다운 파일도 변환 파이프라인 재실행 시 자동으로 일관성 있게 처리됨.
- 향후 노션→휴고 변환 과정에서 title 볼드 표기 문제 재발 방지.

## 참고

- 관련 파일: `src/markdown_converter.py`
- 적용일: 2025-06-22
