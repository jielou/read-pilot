#!/usr/bin/env python3
"""Render a reusable no-API-key Chrome extension for local reading notes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONTENT_JS = r"""
(async function () {
  document.getElementById('reading-companion-root')?.remove();
  document.getElementById('reading-companion-launcher')?.remove();

  const API_BASE = 'http://127.0.0.1:8765';
  const currentUrl = window.location.href.split('#')[0];

  function escapeText(value) {
    return String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function list(items) {
    if (!items || !items.length) return '<p class="rc-muted">No notes yet.</p>';
    return '<ul>' + items.map(item => `<li>${escapeText(item)}</li>`).join('') + '</ul>';
  }

  function normalizeText(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function findHeading(title) {
    const headings = [...document.querySelectorAll('h1,h2,h3,h4')];
    const target = normalizeText(title);
    if (!target) return null;
    return headings.find(node => {
      const text = normalizeText(node.textContent);
      return text === target || (target.length > 8 && text.includes(target)) || (text.length > 8 && target.includes(text));
    }) || null;
  }

  function jumpToSection(title) {
    const heading = findHeading(title);
    if (heading) heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return heading;
  }

  function shell(content) {
    return `
      <div class="rc-header">
        <div>
          <div class="rc-kicker">Read Pilot</div>
          <div class="rc-title">太子伴读</div>
        </div>
        <button class="rc-toggle" type="button" aria-label="Toggle panel">×</button>
      </div>
      <div class="rc-body">${content}</div>
    `;
  }

  function renderMissing() {
    return shell(`
      <section class="rc-card">
        <h2>No Notes Found</h2>
        <p>This URL is not in your local reading library yet.</p>
        <p class="rc-muted">Ask Codex to use $read-pilot for this URL, then refresh this page.</p>
      </section>
      <section class="rc-card">
        <h2>Current URL</h2>
        <p class="rc-url">${escapeText(currentUrl)}</p>
      </section>
    `);
  }

  function renderError(error) {
    return shell(`
      <section class="rc-card">
        <h2>Local Server Offline</h2>
        <p>Start the reading library server, then refresh this page.</p>
        <p class="rc-muted">Expected: ${API_BASE}</p>
      </section>
      <section class="rc-card">
        <h2>Error</h2>
        <p class="rc-url">${escapeText(error.message || String(error))}</p>
      </section>
    `);
  }

  function termsForSection(article, section) {
    return (article.glossary || [])
      .filter(term => !term.section_id || term.section_id === section?.id)
      .slice(0, 6);
  }

  function renderCurrentSection(article, section) {
    if (!section) {
      return `
        <div class="rc-view-actions">
          <button class="rc-secondary" type="button" data-show-overview>Overview</button>
        </div>
        <section class="rc-card rc-current">
          <h2>Current Section</h2>
          <p class="rc-muted">Scroll the article to sync notes with the section you are reading.</p>
        </section>
      `;
    }
    const terms = termsForSection(article, section);
    return `
      <div class="rc-view-actions">
        <button class="rc-secondary" type="button" data-show-overview>Overview</button>
      </div>
      <section class="rc-card rc-current">
        <h2>Current Section</h2>
        <div class="rc-current-title">${escapeText(section.title)}</div>
        <p>${escapeText(section.summary_zh)}</p>
        <h3>Key Points</h3>
        ${list(section.key_points)}
        ${(section.blocks || []).map(block => `
          <div class="rc-focus">
            <strong>${escapeText(block.text)}</strong>
            <p>${escapeText(block.note_zh)}</p>
          </div>
        `).join('')}
        <h3>Why It Matters</h3>
        <p>${escapeText(section.why_it_matters)}</p>
        <h3>Terms</h3>
        ${terms.length ? terms.map(term => `
          <div class="rc-term">
            <strong>${escapeText(term.term)} · ${escapeText(term.translation)}</strong>
            <p>${escapeText(term.explanation)}</p>
          </div>
        `).join('') : '<p class="rc-muted">No terms for this section.</p>'}
        <h3>Recall</h3>
        ${list(section.review_questions)}
      </section>
    `;
  }

  function renderOverview(article) {
    const structureMap = (article.structure_map || []).map(item => `
      <li>
        <strong>${escapeText(item.label)}</strong>
        <span>${escapeText(item.description)}</span>
      </li>
    `).join('');
    return `
      <section class="rc-card">
        <h2>Outline</h2>
        <div class="rc-outline">
          ${(article.sections || []).map(section => `<button type="button" data-section-title="${escapeText(section.title)}">${escapeText(section.title)}</button>`).join('')}
        </div>
      </section>
      <section class="rc-card">
        <h2>Article Map</h2>
        ${structureMap ? `<ul class="rc-map">${structureMap}</ul>` : '<p class="rc-muted">No article map yet.</p>'}
      </section>
      <section class="rc-card">
        <h2>One-Pass Summary</h2>
        <p>${escapeText(article.summary?.one_sentence)}</p>
        <p>${escapeText(article.summary?.high_level)}</p>
      </section>
      <section class="rc-card">
        <h2>Takeaways</h2>
        ${list(article.summary?.takeaways)}
      </section>
      <section class="rc-card">
        <h2>Glossary</h2>
        ${(article.glossary || []).map(term => `
          <div class="rc-term">
            <strong>${escapeText(term.term)} · ${escapeText(term.translation)}</strong>
            <p>${escapeText(term.explanation)}</p>
          </div>
        `).join('')}
      </section>
    `;
  }

  function renderArticle(article) {
    return `
      <div class="rc-header">
        <div>
          <div class="rc-kicker">Read Pilot</div>
          <div class="rc-title">${escapeText(article.title)}</div>
        </div>
        <button class="rc-toggle" type="button" aria-label="Toggle panel">×</button>
      </div>
      <div class="rc-body">
        <div id="rc-panel-content">${renderOverview(article)}</div>
      </div>
    `;
  }

  let currentSectionId = '';
  let panelMode = 'overview';

  function bindPanelControls(article) {
    root.querySelectorAll('[data-section-title]').forEach(button => {
      button.addEventListener('click', () => {
        const section = (article?.sections || []).find(item => normalizeText(item.title) === normalizeText(button.dataset.sectionTitle));
        if (section) showSection(article, section, { scrollPanelTop: true });
        jumpToSection(button.dataset.sectionTitle);
      });
    });
    root.querySelectorAll('[data-show-overview]').forEach(button => {
      button.addEventListener('click', () => showOverview(article));
    });
  }

  function showOverview(article) {
    panelMode = 'overview';
    currentSectionId = '';
    const content = document.getElementById('rc-panel-content');
    if (content) content.innerHTML = renderOverview(article);
    const body = root.querySelector('.rc-body');
    if (body) body.scrollTo({ top: 0, behavior: 'smooth' });
    bindPanelControls(article);
  }

  function showSection(article, section, options = {}) {
    if (!section) return;
    const changed = section.id !== currentSectionId;
    currentSectionId = section.id;
    panelMode = 'section';
    const content = document.getElementById('rc-panel-content');
    if (content) content.innerHTML = renderCurrentSection(article, section);
    root.querySelectorAll('[data-section-title]').forEach(button => {
      button.classList.toggle('active', normalizeText(button.dataset.sectionTitle) === normalizeText(section.title));
    });
    if (changed || options.scrollPanelTop) {
      const body = root.querySelector('.rc-body');
      if (body) body.scrollTo({ top: 0, behavior: 'smooth' });
    }
    bindPanelControls(article);
  }

  function setupScrollSync(article) {
    const anchors = (article.sections || [])
      .map(section => ({ section, heading: findHeading(section.title) }))
      .filter(item => item.heading);

    if (!anchors.length) return;

    let activeId = '';
    let ticking = false;

    function detectCurrentSection() {
      const marker = Math.max(140, window.innerHeight * 0.22);
      if (anchors[0].heading.getBoundingClientRect().top > marker) {
        if (panelMode !== 'overview') showOverview(article);
        activeId = '';
        return;
      }
      let current = anchors[0].section;
      for (const item of anchors) {
        const top = item.heading.getBoundingClientRect().top;
        if (top <= marker) current = item.section;
        else break;
      }
      if (current.id !== activeId) {
        activeId = current.id;
        showSection(article, current);
      }
    }

    window.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        detectCurrentSection();
        ticking = false;
      });
    }, { passive: true });

    window.addEventListener('resize', detectCurrentSection, { passive: true });
    detectCurrentSection();
  }

  async function getArticle() {
    const response = await fetch(`${API_BASE}/api/notes?url=${encodeURIComponent(currentUrl)}`);
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  }

  const root = document.createElement('aside');
  root.id = 'reading-companion-root';
  root.innerHTML = shell('<section class="rc-card"><h2>Loading</h2><p>Checking your local reading library...</p></section>');

  const launcher = document.createElement('button');
  launcher.id = 'reading-companion-launcher';
  launcher.type = 'button';
  launcher.textContent = 'Notes';

  document.documentElement.appendChild(root);
  document.documentElement.appendChild(launcher);
  document.documentElement.classList.add('reading-companion-open');

  function bindControls(article) {
    root.querySelector('.rc-toggle')?.addEventListener('click', () => {
      document.documentElement.classList.remove('reading-companion-open');
    });
    if (article) bindPanelControls(article);
  }

  launcher.addEventListener('click', () => {
    document.documentElement.classList.add('reading-companion-open');
  });

  try {
    const article = await getArticle();
    root.innerHTML = article ? renderArticle(article) : renderMissing();
    if (article) setupScrollSync(article);
    bindControls(article);
  } catch (error) {
    root.innerHTML = renderError(error);
    bindControls(null);
  }
})();
"""


POPUP_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Read Pilot</title>
  <style>
    body {
      width: 280px;
      margin: 0;
      padding: 14px;
      color: #202124;
      background: #fbfaf7;
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    h1 {
      font-size: 16px;
      line-height: 1.25;
      margin: 0 0 8px;
    }
    p {
      margin: 0 0 12px;
      color: #596168;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 7px;
      background: #0f766e;
      color: white;
      cursor: pointer;
      font: 750 14px/1 ui-sans-serif, system-ui, sans-serif;
      padding: 11px 12px;
    }
    button:disabled {
      cursor: default;
      opacity: .65;
    }
    #status {
      min-height: 18px;
      margin-top: 10px;
      color: #596168;
      overflow-wrap: anywhere;
    }
  </style>
</head>
<body>
  <h1>Read Pilot</h1>
  <p>Activate notes for the current tab only.</p>
  <button id="activate" type="button">Show Notes</button>
  <div id="status"></div>
  <script src="popup.js"></script>
</body>
</html>
"""


POPUP_JS = r"""
const button = document.getElementById('activate');
const status = document.getElementById('status');

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function setStatus(message) {
  status.textContent = message;
}

button.addEventListener('click', async () => {
  button.disabled = true;
  setStatus('Activating...');
  try {
    const tab = await activeTab();
    if (!tab?.id || !/^https?:\/\//.test(tab.url || '')) {
      setStatus('Open an http/https article page first.');
      return;
    }
    await chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ['style.css'],
    });
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js'],
    });
    setStatus('Notes activated on this tab.');
  } catch (error) {
    setStatus(error?.message || String(error));
  } finally {
    button.disabled = false;
  }
});
"""


STYLE_CSS = r"""
#reading-companion-root {
  position: fixed;
  z-index: 2147483646;
  top: 0;
  right: 0;
  width: 420px;
  height: 100vh;
  background: #fbfaf7;
  color: #202124;
  border-left: 1px solid #d8d4cb;
  box-shadow: -12px 0 30px rgba(32, 33, 36, .14);
  font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  transform: translateX(100%);
  transition: transform .18s ease;
}
html.reading-companion-open #reading-companion-root {
  transform: translateX(0);
}
#reading-companion-root * {
  box-sizing: border-box;
}
.rc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #d8d4cb;
}
.rc-kicker {
  color: #0f766e;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.rc-title {
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
  margin-top: 4px;
}
.rc-toggle {
  appearance: none;
  border: 1px solid #d8d4cb;
  background: #fffefa;
  color: #202124;
  border-radius: 6px;
  width: 30px;
  height: 30px;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}
.rc-body {
  height: calc(100vh - 75px);
  overflow: auto;
  padding: 16px;
}
.rc-card {
  border-bottom: 1px solid #d8d4cb;
  padding: 0 0 16px;
  margin: 0 0 16px;
}
.rc-view-actions {
  display: flex;
  justify-content: flex-start;
  margin: 0 0 10px;
}
.rc-secondary {
  appearance: none;
  border: 1px solid #d8d4cb;
  background: #fffefa;
  color: #0b4f4a;
  border-radius: 7px;
  cursor: pointer;
  font: 720 13px/1 ui-sans-serif, system-ui, sans-serif;
  padding: 8px 10px;
}
.rc-secondary:hover {
  border-color: #0f766e;
}
.rc-current {
  background: #fffefa;
  border: 1px solid #d8d4cb;
  border-left: 4px solid #0f766e;
  border-radius: 8px;
  padding: 13px 14px 15px;
}
.rc-current-title {
  color: #202124;
  font-size: 18px;
  font-weight: 760;
  line-height: 1.25;
  margin: 0 0 8px;
}
.rc-card h2 {
  color: #0b4f4a;
  font-size: 14px;
  line-height: 1.25;
  margin: 0 0 9px;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.rc-card h3 {
  color: #0b4f4a;
  font-size: 13px;
  margin: 12px 0 6px;
}
.rc-card p,
.rc-card li {
  font-size: 15px;
  line-height: 1.55;
}
.rc-card ul {
  padding-left: 20px;
  margin: 8px 0;
}
.rc-map {
  display: grid;
  gap: 8px;
  list-style: none;
  padding-left: 0 !important;
}
.rc-map li {
  border-left: 3px solid #d8d4cb;
  padding-left: 9px;
}
.rc-map strong {
  display: block;
  color: #202124;
}
.rc-map span {
  display: block;
  color: #596168;
}
.rc-outline {
  display: grid;
  gap: 6px;
}
.rc-outline button {
  appearance: none;
  border: 0;
  background: transparent;
  color: #596168;
  cursor: pointer;
  font: inherit;
  text-align: left;
  padding: 4px 0;
}
.rc-outline button:hover {
  color: #0b4f4a;
}
.rc-outline button.active {
  color: #0b4f4a;
  font-weight: 760;
  border-left: 3px solid #0f766e;
  padding-left: 8px;
}
.rc-focus {
  background: #fff4d8;
  border-left: 3px solid #0f766e;
  padding: 9px 10px;
  margin: 10px 0;
}
.rc-focus strong {
  display: block;
  line-height: 1.45;
}
.rc-term {
  margin: 0 0 10px;
}
.rc-term strong {
  display: block;
}
.rc-term p {
  margin: 4px 0 0;
}
.rc-muted,
.rc-url {
  color: #687076;
}
.rc-url {
  overflow-wrap: anywhere;
}
#reading-companion-launcher {
  position: fixed;
  z-index: 2147483645;
  right: 16px;
  bottom: 16px;
  appearance: none;
  border: 1px solid #0f766e;
  background: #0f766e;
  color: white;
  border-radius: 999px;
  padding: 9px 13px;
  cursor: pointer;
  font: 700 14px/1 ui-sans-serif, system-ui, sans-serif;
  box-shadow: 0 8px 24px rgba(32, 33, 36, .18);
}
html.reading-companion-open #reading-companion-launcher {
  display: none;
}
@media (max-width: 900px) {
  #reading-companion-root {
    width: min(420px, 100vw);
  }
}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Output extension directory")
    parser.add_argument("--api-port", type=int, default=8765, help="Local reading server port")
    args = parser.parse_args()

    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": 3,
        "name": "Read Pilot",
        "version": "1.0.0",
        "description": "Shows local guided reading notes beside matching technical blog pages.",
        "permissions": ["activeTab", "scripting"],
        "host_permissions": [f"http://127.0.0.1:{args.api_port}/*"],
        "action": {"default_popup": "popup.html"},
    }

    content_js = CONTENT_JS.replace("http://127.0.0.1:8765", f"http://127.0.0.1:{args.api_port}")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "content.js").write_text(content_js.lstrip(), encoding="utf-8")
    (out / "popup.html").write_text(POPUP_HTML.lstrip(), encoding="utf-8")
    (out / "popup.js").write_text(POPUP_JS.lstrip(), encoding="utf-8")
    (out / "style.css").write_text(STYLE_CSS.lstrip(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
