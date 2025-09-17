#!/usr/bin/env python3
"""
Tiny E2E smoke for the web KG page.

Checks that the Next.js app is serving /kg and that the page HTML contains
the expected title text. Assumes the web dev server is running on port 3000.

Usage:
  python scripts/smoke_web_kg.py

Environment variables:
  WEB_BASE_URL  Base URL for the web app (default http://127.0.0.1:3000)
  TIMEOUT_SEC   Request timeout in seconds (default 5)
"""
import os
import sys
import time
import urllib.request


def fetch(url: str, timeout: float = 5.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "aurora-smoke/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - local smoke
        code = resp.getcode()
        body = resp.read().decode("utf-8", errors="replace")
        return code, body


def main() -> int:
    base = os.environ.get("WEB_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
    timeout = float(os.environ.get("TIMEOUT_SEC", "5"))
    url = f"{base}/kg"
    # Retry a couple times in case dev server is still booting
    last_err = None
    for attempt in range(3):
        try:
            code, body = fetch(url, timeout=timeout)
            if code != 200:
                print(f"[smoke-web-kg] Unexpected status {code} for {url}", file=sys.stderr)
                return 2
            if "KG Explorer" not in body:
                print(f"[smoke-web-kg] Page loaded but did not contain expected text 'KG Explorer'", file=sys.stderr)
                return 3
            print(f"[smoke-web-kg] PASS: {url} OK and contains title")
            return 0
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    print(f"[smoke-web-kg] FAIL: Could not reach {url}: {last_err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
