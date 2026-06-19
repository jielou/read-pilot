#!/usr/bin/env python3
"""Fetch a technical article URL and produce draft reading-helper JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag


BOILERPLATE_HEADINGS = {
    "get the developer newsletter",
    "newsletter",
    "subscribe",
    "related posts",
    "recommended",
    "more from",
}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value[:80] or "article"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def first_meta(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return ""


def find_article_root(soup: BeautifulSoup) -> Tag:
    for selector in ("article", "main", '[role="main"]'):
        root = soup.select_one(selector)
        if root:
            return root
    return soup.body or soup


def should_stop_at_heading(text: str) -> bool:
    normalized = clean_text(text).lower()
    return normalized in BOILERPLATE_HEADINGS


def extract_blocks(root: Tag) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    block_id = 1
    stop = False

    for tag in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "blockquote", "figcaption"]):
        if stop:
            break
        if not isinstance(tag, Tag):
            continue
        if tag.find_parent(["nav", "footer", "header", "aside", "script", "style"]):
            continue

        text = clean_text(tag.get_text(" ", strip=True))
        if not text:
            continue

        name = tag.name.lower()
        if name in {"h1", "h2", "h3", "h4"}:
            if should_stop_at_heading(text):
                stop = True
                break
            blocks.append(
                {
                    "id": f"h-{block_id:03d}",
                    "type": "heading",
                    "level": int(name[1]),
                    "text": text,
                }
            )
        elif name == "pre":
            blocks.append({"id": f"code-{block_id:03d}", "type": "code", "text": tag.get_text("\n").strip()})
        elif name == "blockquote":
            blocks.append({"id": f"q-{block_id:03d}", "type": "quote", "text": text})
        elif name == "figcaption":
            blocks.append({"id": f"cap-{block_id:03d}", "type": "caption", "text": text})
        elif name == "li":
            blocks.append({"id": f"li-{block_id:03d}", "type": "list_item", "text": text})
        else:
            blocks.append({"id": f"p-{block_id:03d}", "type": "paragraph", "text": text})
        block_id += 1

    return blocks


def sections_from_blocks(blocks: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    section_count = 0

    def new_section(heading: str, level: int) -> dict[str, Any]:
        nonlocal section_count
        section_count += 1
        return {
            "id": slugify(heading) or f"section-{section_count}",
            "level": level,
            "title": heading,
            "summary_zh": "",
            "key_points": [],
            "why_it_matters": "",
            "review_questions": [],
            "blocks": [],
        }

    for block in blocks:
        if block["type"] == "heading":
            if block["level"] == 1 and clean_text(block["text"]).lower() == clean_text(title).lower():
                continue
            if block["level"] <= 3:
                if current:
                    sections.append(current)
                current = new_section(block["text"], block["level"])
                continue

        if current is None:
            current = new_section("Introduction", 2)
        current["blocks"].append(block)

    if current:
        sections.append(current)
    return sections


def build_article(url: str, include_full_text: bool = False) -> dict[str, Any]:
    response = requests.get(url, timeout=30, headers={"User-Agent": "read-pilot/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = first_meta(soup, "og:title", "twitter:title") or clean_text((soup.find("h1") or soup.find("title")).get_text(" ", strip=True))
    subtitle = first_meta(soup, "description", "og:description", "twitter:description")
    author = first_meta(soup, "author", "article:author")
    published = first_meta(soup, "article:published_time", "date", "pubdate")

    root = find_article_root(soup)
    blocks = extract_blocks(root)
    sections = sections_from_blocks(blocks, title)
    if not include_full_text:
        for section in sections:
            section["source_block_count"] = len(section.get("blocks", []))
            section["blocks"] = []

    parsed = urlparse(url)
    slug_source = title or parsed.path.strip("/") or parsed.netloc

    return {
        "schema_version": "1.0",
        "source_url": url,
        "slug": slugify(slug_source),
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "published": published,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "language": "en",
        "summary": {"one_sentence": "", "high_level": "", "takeaways": []},
        "structure_map": [],
        "glossary": [],
        "sections": sections,
        "final_review_questions": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out", required=True, help="Output draft JSON path")
    parser.add_argument(
        "--include-full-text",
        action="store_true",
        help="Store original paragraph/list/code blocks. Use for user-provided, public-domain, or otherwise permitted content.",
    )
    args = parser.parse_args()

    article = build_article(args.url, include_full_text=args.include_full_text)
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
