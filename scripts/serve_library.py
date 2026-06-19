#!/usr/bin/env python3
"""Serve a local reading library and URL-matched notes API."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


def normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return f"{scheme}://{host}{path}"


def load_articles(library: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((library / "data" / "articles").glob("*.json")):
        try:
            articles.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return articles


class Handler(SimpleHTTPRequestHandler):
    library: Path

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.handle_health()
            return
        if parsed.path == "/api/notes":
            self.handle_notes(parsed.query)
            return
        if parsed.path == "/api/articles":
            self.handle_articles()
            return
        super().do_GET()

    def handle_health(self) -> None:
        self.write_json(
            {
                "status": "ok",
                "library": str(self.library),
            }
        )

    def handle_articles(self) -> None:
        articles = load_articles(self.library)
        payload = [
            {
                "title": article.get("title"),
                "source_url": article.get("source_url"),
                "slug": article.get("slug"),
                "published": article.get("published"),
            }
            for article in articles
        ]
        self.write_json(payload)

    def handle_notes(self, query: str) -> None:
        params = parse_qs(query)
        requested = unquote((params.get("url") or [""])[0])
        requested_norm = normalize_url(requested)
        for article in load_articles(self.library):
            source = article.get("source_url", "")
            if normalize_url(source) == requested_norm:
                self.write_json(article)
                return
        self.write_json({"error": "not found", "url": requested}, status=404)

    def write_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, help="Library directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    library = Path(args.library).expanduser().resolve()
    Handler.library = library

    import os

    os.chdir(library)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving {library} at http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
