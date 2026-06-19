---
name: read-pilot
description: Turn long technical blog posts, engineering articles, research explainers, or saved HTML/Markdown into a local guided reading system with a blog library, reusable Chrome extension side panel, high-level summaries, section-by-section Chinese notes, glossary entries, paragraph annotations, review questions, and optional offline archive pages. Use when the user gives a URL or article file and wants help reading, understanding, translating, annotating, studying, archiving, or building a local library for technical English articles.
---

# Read Pilot

## Overview

Read Pilot, 中文名“太子伴读”, creates a local reading library for technical articles. Prefer live-page reading: the user reads the original article in Chrome, then activates a reusable local extension popup for that tab to show companion notes from the local library side panel. Use offline archive pages only when the user explicitly wants local source text and has rights to transform it.

## Default Workflow

1. Fetch or ingest the article.
   - For ordinary online URLs, run `scripts/fetch_article.py <url> --out <work-dir>/<slug>.draft.json` to create a companion draft with metadata and section structure.
   - For user-provided local files, public-domain content, or content the user has rights to transform, use `--include-full-text` if the final offline page should contain the original prose.
   - For copyrighted online articles, create an offline companion page with summaries, notes, glossary, and short section structure rather than reproducing the full article text.
2. Inspect and clean the draft.
   - Remove newsletter, nav, footer, repeated boilerplate, or unrelated link lists.
   - Keep code blocks, lists, figures, captions, and section hierarchy when relevant.
3. Fill the guided reading fields in JSON.
   - Add a one-sentence thesis, high-level summary, article map, takeaways, terms, section summaries, and review questions.
   - Add paragraph notes selectively for dense or important paragraphs; do not annotate every sentence unless the user asks.
4. Render the library and reusable live-page extension.
   - Run `scripts/render_library.py --library <library-dir> --article <article-json>`.
   - Run `scripts/render_chrome_extension.py --out <library-dir>/extension`.
   - Run `scripts/ensure_server.py --library <library-dir> --port 8765` to start or reuse the local server automatically.
   - The HTML renderer creates a homepage and note detail pages for managing the library.
   - The Chrome extension is generic, installed once, and does nothing until the user opens the extension popup and clicks the activation button for the current tab.
   - After activation, the side panel syncs to the current article section while the user scrolls the live page.
   - Do not create one extension per article unless explicitly requested.
5. Verify the output.
   - Prefer `scripts/ensure_server.py --library <library-dir> --port 8765`; it checks whether the server is already running and starts it in the background if needed.
   - Check `http://127.0.0.1:8765/` for the library homepage.
   - Check `http://127.0.0.1:8765/api/notes?url=<encoded-source-url>` returns the article JSON.
   - The user only needs to load `<library-dir>/extension` once as an unpacked Chrome extension. After that, tell them to open the source URL, click the Read Pilot extension, and click the activation button.

## Reading Note Style

Write Chinese notes for comprehension, not replacement.

- Start with the article's structure: what problem is introduced, what solution is proposed, what evidence or examples support it, and what remains open.
- Keep summaries concise and concrete. Avoid generic praise, vague "this section discusses..." wording, and decorative language.
- Prefer "意译 + 技术解释" for difficult English rather than full literal translation.
- Explain key English terms with the original term first, then Chinese meaning, then why it matters in the article.
- Surface assumptions and missing context. For technical posts, briefly explain related concepts only when needed to understand the author's argument.
- Add recall questions after sections so the user can test understanding before continuing.

## JSON Contract

Use `references/article_json_schema.md` when creating or repairing article JSON. The renderer is tolerant of missing fields, but high-quality pages should include:

- `summary.one_sentence`
- `summary.high_level`
- `summary.takeaways`
- `structure_map`
- `glossary`
- `sections[].summary_zh`
- `sections[].key_points`
- `sections[].why_it_matters`
- `sections[].review_questions`
- selected `sections[].blocks[].note_zh`
- selected `sections[].blocks[].translation_zh`

## Local Library Conventions

- Use one folder per reading library, usually `<workspace>/library`.
- Keep source JSON in `<library>/data/articles/`.
- Generated pages live at `<library>/index.html` and `<library>/articles/<slug>.html`.
- The reusable Chrome extension lives at `<library>/extension`.
- The local notes API is served on `http://127.0.0.1:8765` by default.
- Use `scripts/ensure_server.py` after every render so the user does not need to manage `serve_library.py` manually.
- Do not overwrite unrelated existing article JSON unless the user asks to regenerate it.
- Slugs should be stable, lowercase, and URL-safe.

## Resources

- `scripts/fetch_article.py`: fetch a URL and produce a draft article JSON with metadata and sections; `--include-full-text` also stores paragraph blocks.
- `scripts/render_library.py`: render one or more article JSON files into a self-contained local HTML library.
- `scripts/render_chrome_extension.py`: render a reusable no-API-key Chrome extension with a popup activation button; when activated for the current tab, it loads notes from the local library server, injects them into the original article page, and updates current-section notes while scrolling.
- `scripts/serve_library.py`: serve the local library homepage and URL-matched notes API.
- `scripts/ensure_server.py`: check whether the local server is already running for the requested library; if not, start `serve_library.py` in the background and report the local URL.
- `references/article_json_schema.md`: field guide for article JSON.
