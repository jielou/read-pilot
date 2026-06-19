# Article JSON Schema

The renderer accepts partial data, but use this structure for consistent guided reading pages.

```json
{
  "schema_version": "1.0",
  "source_url": "https://example.com/post",
  "slug": "example-post",
  "title": "Article title",
  "subtitle": "Optional dek or subtitle",
  "author": "Author name",
  "published": "Published date as shown by source",
  "captured_at": "ISO timestamp",
  "language": "en",
  "summary": {
    "one_sentence": "Chinese or bilingual thesis.",
    "high_level": "Short Chinese overview.",
    "takeaways": ["Takeaway 1", "Takeaway 2"]
  },
  "structure_map": [
    {
      "label": "Problem",
      "sections": ["section-id"],
      "description": "What this part does in the argument."
    }
  ],
  "glossary": [
    {
      "term": "context window",
      "translation": "上下文窗口",
      "explanation": "Meaning in this article.",
      "section_id": "optional-section-id"
    }
  ],
  "sections": [
    {
      "id": "section-id",
      "level": 2,
      "title": "Section title",
      "summary_zh": "Chinese section summary.",
      "key_points": ["Point 1", "Point 2"],
      "why_it_matters": "Why this section matters.",
      "review_questions": ["Question 1"],
      "blocks": [
        {
          "id": "p-001",
          "type": "paragraph",
          "text": "Original paragraph text.",
          "note_zh": "Optional Chinese explanation.",
          "translation_zh": "Optional Chinese meaning translation."
        }
      ]
    }
  ],
  "final_review_questions": ["Question 1"]
}
```

## Block Types

Use these block types:

- `paragraph`: normal prose.
- `list_item`: one list item from the article.
- `code`: code, JSON, command, or config block.
- `quote`: quoted article text.
- `caption`: figure or image caption.

## Annotation Guidance

Annotate selectively:

- Add `note_zh` to paragraphs that carry the main argument, introduce a technical concept, or may be difficult for a non-native English reader.
- Add `translation_zh` when the English syntax is dense or the paragraph is worth reading closely.
- Leave obvious paragraphs unannotated so the side panel stays focused.
