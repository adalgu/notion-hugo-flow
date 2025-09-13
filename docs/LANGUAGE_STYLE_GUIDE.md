# Notion-Hugo Language Style Guide

## Language Principles
- Use clear, professional English
- Avoid overly technical jargon
- Write for a global, technical audience
- Be concise and precise

## Terminology Standards
- **Metadata**: Use this term consistently (not "meta data" or "meta-data")
- **Database ID**: Always use this exact phrase
- **Synchronization**: Preferred over "Sync" in formal documentation
- **Configuration**: Use instead of "Config" in official docs

## Documentation Tone
- Professional but approachable
- Use active voice
- Explain "why" not just "how"
- Provide context for technical decisions

## Comment Style (Python)
- Use English for all comments
- Start with a capital letter
- End with a period
- Explain the purpose, not just restate the code
- Use type hints and docstrings

## Examples

### Good Comment
```python
# Converts Notion page properties to Hugo-compatible markdown metadata.
# Handles complex property mappings and ensures consistent formatting.
def convert_notion_metadata(page_properties: Dict[str, Any]) -> Dict[str, str]:
    """
    Transform Notion page properties into Hugo front matter.

    Args:
        page_properties: Raw Notion page property dictionary
    Returns:
        Processed Hugo front matter dictionary
    """
```

### Avoid
```python
# 페이지 속성 변환 (Bad: Korean comment)
# Convert properties (Vague comment)
def convert(props):  # Lacks type hints
    pass
```

## Common Translation Patterns
- "메타데이터" → "Metadata"
- "동기화" → "Synchronization"
- "설정" → "Configuration"

## Writing Guidelines
1. Be specific
2. Avoid ambiguity
3. Provide context
4. Use standard technical terminology