#!/usr/bin/env python3
"""Render guided technical-article JSON files into a local HTML library."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


STYLE = """
:root {
  color-scheme: light;
  --bg: #f6f5f1;
  --paper: #fffefa;
  --ink: #202124;
  --muted: #687076;
  --line: #d8d4cb;
  --accent: #0f766e;
  --accent-ink: #0b4f4a;
  --note: #fff4d8;
  --code: #102027;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--bg);
}
a { color: inherit; }
.library-shell { max-width: 1180px; margin: 0 auto; padding: 32px 22px 56px; }
.topbar { display: flex; align-items: baseline; justify-content: space-between; gap: 18px; border-bottom: 1px solid var(--line); padding-bottom: 18px; }
.brand { font-size: 24px; font-weight: 720; }
.muted { color: var(--muted); }
.article-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-top: 24px; }
.article-card { display: block; text-decoration: none; background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 18px; min-height: 210px; }
.article-card:hover { border-color: var(--accent); }
.article-card h2 { font-size: 19px; line-height: 1.25; margin: 0 0 10px; }
.article-card p { line-height: 1.5; margin: 0 0 12px; }
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.chip { font-size: 12px; padding: 4px 7px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); }
.reader-shell { display: grid; grid-template-columns: minmax(480px, 1fr) 430px; min-height: 100vh; }
.reader-main { min-height: 100vh; display: grid; grid-template-rows: auto 1fr; background: var(--paper); }
.reader-side { height: 100vh; overflow: auto; border-left: 1px solid var(--line); background: #fbfaf7; padding: 22px; }
.article-nav { display: flex; justify-content: space-between; gap: 14px; margin-bottom: 22px; color: var(--muted); font-size: 14px; }
.source-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 56px; padding: 12px 16px; border-bottom: 1px solid var(--line); background: #fbfaf7; }
.source-toolbar a { color: var(--accent-ink); font-weight: 650; text-decoration: none; }
.source-title { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 680; }
.source-frame-wrap { min-height: 0; }
.source-frame { width: 100%; height: calc(100vh - 57px); border: 0; background: white; }
.article-title { font-size: 28px; line-height: 1.1; margin: 4px 0 12px; max-width: 920px; letter-spacing: 0; }
.dek { max-width: 850px; font-size: 19px; line-height: 1.55; color: #444b50; }
.meta { margin: 16px 0 26px; color: var(--muted); }
.summary-band { border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 16px 0; margin: 18px 0 22px; display: grid; grid-template-columns: 1fr; gap: 16px; }
.summary-band h2, .side-panel h2 { margin: 0 0 10px; font-size: 16px; text-transform: uppercase; letter-spacing: .04em; color: var(--accent-ink); }
.summary-band p, .summary-band li { line-height: 1.55; }
.article-section { margin-top: 22px; padding-top: 12px; border-top: 1px solid var(--line); }
.article-section h2 { font-size: 22px; line-height: 1.2; margin: 0 0 12px; }
.article-section h3 { font-size: 19px; line-height: 1.25; margin: 18px 0 10px; }
.section-summary { line-height: 1.58; margin: 0 0 12px; }
.compact-list { margin: 8px 0 0; padding-left: 20px; }
.compact-list li { line-height: 1.5; margin: 5px 0; }
.block { max-width: 850px; font-size: 15px; line-height: 1.58; margin: 9px 0; padding: 8px 10px; border-left: 3px solid transparent; cursor: pointer; background: #fffaf0; }
.block:hover { background: #eeebe3; }
.block.active { background: var(--note); border-left-color: var(--accent); }
.block.list-item { margin-left: 18px; }
pre.block { white-space: pre-wrap; background: var(--code); color: #ecf6f2; padding: 14px; border-radius: 6px; overflow: auto; font-size: 14px; line-height: 1.5; cursor: text; }
.caption { color: var(--muted); font-size: 14px; }
.side-panel { display: grid; gap: 18px; }
.side-card { border-bottom: 1px solid var(--line); padding-bottom: 16px; }
.side-card h3 { margin: 0 0 8px; font-size: 18px; }
.side-card p, .side-card li { line-height: 1.55; }
.outline { display: grid; gap: 7px; }
.outline button { text-align: left; border: 0; background: transparent; color: var(--muted); padding: 5px 0; cursor: pointer; font: inherit; }
.outline button:hover { color: var(--accent-ink); }
.term { margin-bottom: 10px; }
.term strong { display: block; }
.selected-note { background: var(--note); border: 1px solid #eadca8; border-radius: 8px; padding: 12px; }
.empty-note { color: var(--muted); }
@media (max-width: 920px) {
  .reader-shell { display: block; }
  .reader-side { height: auto; border-left: 0; border-top: 1px solid var(--line); }
  .source-frame { height: 72vh; }
  .summary-band { grid-template-columns: 1fr; }
}
"""


SCRIPT = """
const article = ARTICLE_DATA;
const sectionById = new Map(article.sections.map(section => [section.id, section]));
const blockById = new Map();
for (const section of article.sections) {
  for (const block of section.blocks || []) blockById.set(block.id, { section, block });
}
let selectedBlockId = null;

function escapeText(value) {
  return String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function list(items) {
  if (!items || !items.length) return '<p class="empty-note">No notes yet.</p>';
  return '<ul>' + items.map(item => `<li>${escapeText(item)}</li>`).join('') + '</ul>';
}

function renderSide(sectionId, blockId) {
  const section = sectionById.get(sectionId) || article.sections[0];
  const selected = blockId ? blockById.get(blockId)?.block : null;
  const terms = (article.glossary || []).filter(term => !term.section_id || term.section_id === section.id).slice(0, 6);
  document.getElementById('side').innerHTML = `
    <div class="side-panel">
      <div class="side-card">
        <h2>Current Section</h2>
        <h3>${escapeText(section.title)}</h3>
        <p>${escapeText(section.summary_zh || '')}</p>
      </div>
      <div class="side-card">
        <h2>Key Points</h2>
        ${list(section.key_points)}
      </div>
      <div class="side-card">
        <h2>Why It Matters</h2>
        <p>${escapeText(section.why_it_matters || 'No note yet.')}</p>
      </div>
      <div class="side-card">
        <h2>Selected Paragraph</h2>
        ${selected ? `
          <div class="selected-note">
            <p><strong>意译</strong><br>${escapeText(selected.translation_zh || '这一段暂时没有单独翻译。')}</p>
            <p><strong>理解提示</strong><br>${escapeText(selected.note_zh || '这一段可以按原文顺读。')}</p>
          </div>
        ` : '<p class="empty-note">Click a paragraph to see focused notes.</p>'}
      </div>
      <div class="side-card">
        <h2>Terms</h2>
        ${terms.length ? terms.map(term => `
          <div class="term">
            <strong>${escapeText(term.term)} · ${escapeText(term.translation || '')}</strong>
            <span>${escapeText(term.explanation || '')}</span>
          </div>
        `).join('') : '<p class="empty-note">No terms for this section.</p>'}
      </div>
      <div class="side-card">
        <h2>Recall</h2>
        ${list(section.review_questions)}
      </div>
    </div>
  `;
}

document.querySelectorAll('[data-block-id]').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('.block.active').forEach(node => node.classList.remove('active'));
    el.classList.add('active');
    selectedBlockId = el.dataset.blockId;
    renderSide(el.dataset.sectionId, el.dataset.blockId);
  });
});

document.querySelectorAll('[data-jump-section]').forEach(button => {
  button.addEventListener('click', () => {
    const section = document.getElementById(button.dataset.jumpSection);
    if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    selectedBlockId = null;
    renderSide(button.dataset.jumpSection, null);
  });
});

const observer = new IntersectionObserver(entries => {
  const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (visible) {
    const selected = selectedBlockId ? blockById.get(selectedBlockId) : null;
    const selectedInVisibleSection = selected?.section?.id === visible.target.id ? selectedBlockId : null;
    renderSide(visible.target.id, selectedInVisibleSection);
  }
}, { threshold: [0.25, 0.5, 0.75] });
document.querySelectorAll('.article-section').forEach(section => observer.observe(section));
renderSide(article.sections[0]?.id, null);
"""


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def load_article(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def block_html(block: dict[str, Any], section_id: str) -> str:
    text = esc(block.get("text", ""))
    block_id = esc(block.get("id", ""))
    block_type = block.get("type", "paragraph")
    classes = f"block {esc(block_type.replace('_', '-'))}"
    attrs = f'data-section-id="{esc(section_id)}" data-block-id="{block_id}"'
    if block_type == "code":
        return f"<pre class=\"{classes}\" {attrs}><code>{text}</code></pre>"
    if block_type == "list_item":
        return f"<p class=\"{classes}\" {attrs}>• {text}</p>"
    if block_type == "quote":
        return f"<blockquote class=\"{classes}\" {attrs}>{text}</blockquote>"
    if block_type == "caption":
        return f"<p class=\"{classes} caption\" {attrs}>{text}</p>"
    return f"<p class=\"{classes}\" {attrs}>{text}</p>"


def render_article(article: dict[str, Any]) -> str:
    summary = article.get("summary", {})
    sections = article.get("sections", [])
    outline = "\n".join(
        f'<button data-jump-section="{esc(section.get("id"))}">{esc(section.get("title"))}</button>'
        for section in sections
    )
    takeaways = "".join(f"<li>{esc(item)}</li>" for item in summary.get("takeaways", []))
    structure = "".join(
        f"<li><strong>{esc(item.get('label'))}</strong>: {esc(item.get('description'))}</li>"
        for item in article.get("structure_map", [])
    )
    section_html = []
    for section in sections:
        level = "h2" if int(section.get("level", 2)) <= 2 else "h3"
        blocks = "\n".join(block_html(block, section.get("id", "")) for block in section.get("blocks", []))
        key_points = "".join(f"<li>{esc(item)}</li>" for item in section.get("key_points", []))
        questions = "".join(f"<li>{esc(item)}</li>" for item in section.get("review_questions", []))
        section_html.append(
            f"""
            <section class="article-section" id="{esc(section.get('id'))}">
              <{level}>{esc(section.get('title'))}</{level}>
              <p class="section-summary">{esc(section.get('summary_zh'))}</p>
              <ul class="compact-list">{key_points}</ul>
              {blocks}
              <p class="section-summary"><strong>Why it matters:</strong> {esc(section.get('why_it_matters'))}</p>
              <ul class="compact-list">{questions}</ul>
            </section>
            """
        )
    data = json.dumps(article, ensure_ascii=False)
    script = SCRIPT.replace("ARTICLE_DATA", data)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{esc(article.get('title'))}</title>
  <style>{STYLE}</style>
</head>
<body>
  <div class="reader-shell">
    <main class="reader-main">
      <div class="source-toolbar">
        <a href="../index.html">Library</a>
        <div class="source-title">{esc(article.get('title'))}</div>
        <a href="{esc(article.get('source_url'))}" target="_blank" rel="noreferrer">Open Original</a>
      </div>
      <div class="source-frame-wrap">
        <iframe class="source-frame" src="{esc(article.get('source_url'))}" title="Original article"></iframe>
      </div>
    </main>
    <aside class="reader-side">
      <nav class="article-nav"><a href="../index.html">Library</a><a href="{esc(article.get('source_url'))}" target="_blank" rel="noreferrer">Original</a></nav>
      <h1 class="article-title">{esc(article.get('title'))}</h1>
      <p class="dek">{esc(article.get('subtitle'))}</p>
      <div class="meta">{esc(article.get('author'))} {esc(article.get('published'))}</div>
      <div id="side"></div>
      <div class="summary-band">
        <section>
          <h2>One-Pass Summary</h2>
          <p>{esc(summary.get('one_sentence'))}</p>
          <p>{esc(summary.get('high_level'))}</p>
        </section>
        <section>
          <h2>Takeaways</h2>
          <ul>{takeaways}</ul>
        </section>
        <section>
          <h2>Structure</h2>
          <ul>{structure}</ul>
        </section>
        <section>
          <h2>Outline</h2>
          <div class="outline">{outline}</div>
        </section>
      </div>
      {''.join(section_html)}
    </aside>
  </div>
  <script>{script}</script>
</body>
</html>"""


def render_index(articles: list[dict[str, Any]]) -> str:
    cards = []
    for article in sorted(articles, key=lambda a: a.get("captured_at", ""), reverse=True):
        summary = article.get("summary", {})
        tags = "".join(f'<span class="chip">{esc(item.get("term"))}</span>' for item in article.get("glossary", [])[:4])
        cards.append(
            f"""
            <a class="article-card" href="articles/{esc(article.get('slug'))}.html">
              <h2>{esc(article.get('title'))}</h2>
              <p class="muted">{esc(article.get('published'))}</p>
              <p>{esc(summary.get('one_sentence') or summary.get('high_level'))}</p>
              <div class="chip-row">{tags}</div>
            </a>
            """
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Reading Library</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="library-shell">
    <header class="topbar">
      <div>
        <div class="brand">Reading Library</div>
        <div class="muted">Offline guided reading for technical blogs</div>
      </div>
      <div class="muted">Updated {esc(datetime.now().strftime('%Y-%m-%d %H:%M'))}</div>
    </header>
    <section class="article-grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, help="Output library directory")
    parser.add_argument("--article", action="append", default=[], help="Article JSON path; can be repeated")
    args = parser.parse_args()

    library = Path(args.library).expanduser()
    data_dir = library / "data" / "articles"
    page_dir = library / "articles"
    data_dir.mkdir(parents=True, exist_ok=True)
    page_dir.mkdir(parents=True, exist_ok=True)

    article_paths = [Path(path).expanduser() for path in args.article]
    if not article_paths:
        article_paths = sorted(data_dir.glob("*.json"))

    articles = []
    for path in article_paths:
        article = load_article(path)
        slug = article.get("slug") or path.stem
        article["slug"] = slug
        (data_dir / f"{slug}.json").write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        (page_dir / f"{slug}.html").write_text(render_article(article), encoding="utf-8")
        articles.append(article)

    (library / "index.html").write_text(render_index(articles), encoding="utf-8")
    print(library / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
