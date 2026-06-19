# AGENTS.md

## Project Purpose

Read Pilot, Chinese name "太子伴读", is a Codex skill plus local Python tooling for turning long technical articles into Chinese guided-reading materials.

The repo supports two usage modes:

- As a Codex skill named `read-pilot`, driven by `SKILL.md`.
- As standalone local scripts that fetch article metadata, render a local HTML reading library, build a reusable Chrome extension, and serve a local notes API.

The intended output is companion reading material, not a full article mirror. For ordinary copyrighted online articles, store summaries, structure, notes, glossary terms, recall questions, and short structural cues. Do not copy full source prose unless the user provided it, it is public domain, or the user has rights to transform it.

## Repository Map

- `SKILL.md`: primary Codex skill instructions and workflow.
- `README.md` / `README.zh-CN.md`: user-facing setup and usage docs.
- `agents/openai.yaml`: skill UI metadata.
- `references/article_json_schema.md`: JSON contract for guided-reading article files.
- `scripts/fetch_article.py`: fetch a URL and generate draft article JSON.
- `scripts/render_library.py`: render article JSON into a local HTML library.
- `scripts/render_chrome_extension.py`: generate the reusable unpacked Chrome extension.
- `scripts/serve_library.py`: serve the rendered library and notes API.
- `scripts/ensure_server.py`: start or reuse the local server for a rendered library.
- `assets/`: logo and extension icons.
- `demo/articles/`: checked-in demo article JSON.

Generated local libraries normally live in `library/` or `.tmp/`; both are ignored. Do not commit generated library pages, logs, drafts, or output artifacts unless the user explicitly asks.

## Setup

Use Python 3.

```bash
python3 -m pip install -r requirements.txt
```

Runtime dependencies are intentionally small:

- `requests`
- `beautifulsoup4`

There is no package manager config, test runner config, or build system beyond the Python scripts.

## Common Workflows

Fetch a draft from a URL:

```bash
python3 scripts/fetch_article.py https://example.com/post --out .tmp/example.draft.json
```

Fetch with full source blocks only when permitted:

```bash
python3 scripts/fetch_article.py https://example.com/post --include-full-text --out .tmp/example.draft.json
```

Render one article into a library:

```bash
python3 scripts/render_library.py --library library --article path/to/article.json
```

Render all articles already in a library:

```bash
python3 scripts/render_library.py --library library
```

Build the reusable Chrome extension:

```bash
python3 scripts/render_chrome_extension.py --out library/extension
```

Serve the local library and notes API:

```bash
python3 scripts/ensure_server.py --library library --port 8765
```

Open the rendered library at:

```text
http://127.0.0.1:8765/
```

The URL-matched notes API is:

```text
http://127.0.0.1:8765/api/notes?url=<encoded-source-url>
```

## Demo Verification

A quick local smoke test uses the checked-in demo JSON and writes only to `.tmp/`:

```bash
python3 scripts/render_library.py --library .tmp/demo-library --article demo/articles/my-ai-adoption-journey.json
python3 scripts/render_chrome_extension.py --out .tmp/demo-library/extension
python3 scripts/ensure_server.py --library .tmp/demo-library --port 8765
```

Then check:

- `http://127.0.0.1:8765/`
- `http://127.0.0.1:8765/api/articles`

Stop the server before finishing the task.

## Article JSON Guidance

Follow `references/article_json_schema.md` for article files. High-quality article JSON should include:

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

Keep Chinese notes concise and explanatory. Prefer "意译 + 技术解释" for difficult English. Add paragraph notes selectively for dense, central, or technically important passages.

## Coding Conventions

- Keep scripts dependency-light and runnable with plain `python3`.
- Prefer the existing single-file script style over adding frameworks.
- Use structured JSON operations rather than ad hoc text manipulation for article data.
- Keep generated HTML/CSS/JS self-contained unless there is a clear reason to introduce new assets.
- Keep slugs stable, lowercase, and URL-safe.
- Do not overwrite unrelated existing article JSON unless the user asks for regeneration.
- Preserve the reusable-extension model: one local Chrome extension reads notes from the local server; do not create one extension per article unless explicitly requested.

## Change Checklist

Before handing off changes:

1. Run the smallest relevant smoke test.
2. If script behavior changed, run the demo render workflow.
3. Use `scripts/ensure_server.py` for server verification unless testing `serve_library.py` directly.
4. Check that generated files stayed in ignored directories such as `.tmp/` or `library/`.
5. Confirm `git status --short` only shows intentional source/documentation changes.
