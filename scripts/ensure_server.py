#!/usr/bin/env python3
"""Ensure the local Read Pilot server is running for a library."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


def health_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/api/health"


def fetch_json(url: str, timeout: float = 1.0) -> dict[str, Any] | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return None


def server_matches_library(host: str, port: int, library: Path) -> bool:
    payload = fetch_json(health_url(host, port))
    if not payload:
        return False
    return Path(str(payload.get("library", ""))).resolve() == library


def wait_until_ready(host: str, port: int, library: Path, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server_matches_library(host, port, library):
            return True
        time.sleep(0.15)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, help="Library directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--wait", type=float, default=6.0, help="Seconds to wait for a new server")
    args = parser.parse_args()

    library = Path(args.library).expanduser().resolve()
    if not library.exists():
        print(f"error: library does not exist: {library}", file=sys.stderr)
        return 1

    existing = fetch_json(health_url(args.host, args.port))
    if existing:
        existing_library = Path(str(existing.get("library", ""))).resolve()
        if existing_library == library:
            print(f"Read Pilot server already running: http://{args.host}:{args.port}/")
            return 0
        print(
            "error: port is already serving a different Read Pilot library: "
            f"{existing_library}",
            file=sys.stderr,
        )
        print(
            "Use the same library, stop the existing server, or choose another port and rebuild the extension with --api-port.",
            file=sys.stderr,
        )
        return 2

    state_dir = library / ".server"
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "read-pilot-server.log"
    pid_path = state_dir / "read-pilot-server.pid"
    serve_script = Path(__file__).resolve().with_name("serve_library.py")
    command = [
        sys.executable,
        str(serve_script),
        "--library",
        str(library),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]

    log_file = log_path.open("ab")
    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    pid_path.write_text(str(process.pid), encoding="utf-8")

    if not wait_until_ready(args.host, args.port, library, args.wait):
        print(f"error: server did not become ready; see {log_path}", file=sys.stderr)
        return 1

    print(f"Read Pilot server started: http://{args.host}:{args.port}/")
    print(f"PID: {process.pid}")
    print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
