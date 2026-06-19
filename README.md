# Read Pilot

Read Pilot, 中文名“太子伴读”, is a Codex skill and local tooling kit for turning long technical articles into guided Chinese reading notes.

It produces:

- structured article JSON with summaries, section notes, glossary terms, and recall questions
- a local HTML reading library
- a reusable Chrome extension that injects companion notes beside the live article page
- a small local notes API for matching the current URL to local article notes

The Codex skill name is `read-pilot`.

## Repository Layout

```text
.
├── SKILL.md                         # Codex skill instructions
├── agents/openai.yaml               # Skill UI metadata
├── references/article_json_schema.md # Article JSON field guide
├── scripts/
│   ├── fetch_article.py             # Fetch URL metadata and section draft
│   ├── render_library.py            # Render article JSON into local HTML pages
│   ├── render_chrome_extension.py   # Build the reusable Chrome extension
│   └── serve_library.py             # Serve pages and URL-matched notes API
└── demo/articles/                   # One checked-in demo article JSON
```

Local generated libraries should stay out of git. By convention, create them in `library/` or `.tmp/`; both are ignored.

## Install Dependencies

Use Python 3. The scripts depend on `requests` and `beautifulsoup4`.

```bash
python3 -m pip install -r requirements.txt
```

## Use As A Codex Skill

Clone or copy this repository into your Codex skills directory as `read-pilot`, then ask Codex to use the skill for a URL.

```bash
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/read-pilot
```

Example prompt:

```text
新增文章解析: https://example.com/post 用本地的 skill
```

## Manual Workflow

Fetch a draft:

```bash
python3 scripts/fetch_article.py https://example.com/post --out .tmp/example.draft.json
```

Fill the guided-reading fields in the JSON using `references/article_json_schema.md`, then save the final article JSON under:

```text
library/data/articles/<slug>.json
```

Render the library and extension:

```bash
python3 scripts/render_library.py --library library
python3 scripts/render_chrome_extension.py --out library/extension
```

Serve locally:

```bash
python3 scripts/serve_library.py --library library --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

The notes API is available at:

```text
http://127.0.0.1:8765/api/notes?url=<encoded-source-url>
```

## Demo

The repo includes one demo article JSON:

```text
demo/articles/my-ai-adoption-journey.json
```

Render it into a temporary local library:

```bash
python3 scripts/render_library.py --library .tmp/demo-library --article demo/articles/my-ai-adoption-journey.json
python3 scripts/render_chrome_extension.py --out .tmp/demo-library/extension
python3 scripts/serve_library.py --library .tmp/demo-library --port 8765
```

Then visit:

```text
http://127.0.0.1:8765/
```

## Content Policy

For ordinary copyrighted online articles, store companion notes, summaries, glossary entries, and short structural cues. Do not copy full article text into local JSON unless the user provided the text, the text is public domain, or the user has rights to transform it.
