#!/usr/bin/env python3
"""
Generate a minimal Postman v2.1 collection from docs/openapi.yaml.

- Uses a baseUrl variable (defaults to http://127.0.0.1:8000).
- Creates requests for each path+method with example placeholders.
- Writes to tmp/aurora_kg_v2.postman_collection.json by default.
"""
import json
import os
import sys
from typing import Dict, Any

try:
    import yaml  # type: ignore
except Exception:
    print("Missing PyYAML. Install with: pip install pyyaml")
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(__file__))
OPENAPI_PATH = os.path.join(ROOT, "docs", "openapi.yaml")
OUT_DIR = os.path.join(ROOT, "tmp")
OUT_PATH = os.path.join(OUT_DIR, "aurora_kg_v2.postman_collection.json")


def load_openapi(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_postman(openapi: Dict[str, Any]) -> Dict[str, Any]:
    name = openapi.get("info", {}).get("title", "AURORA API")
    collection = {
        "info": {
            "name": name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": openapi.get("info", {}).get("version", "0.0.0"),
        },
        "variable": [
            {"key": "baseUrl", "value": "http://127.0.0.1:8000"}
        ],
        "item": [],
    }

    paths = openapi.get("paths", {})
    for path, methods in paths.items():
        folder = {"name": path, "item": []}
        for method, op in (methods or {}).items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            req_name = op.get("summary") or f"{method.upper()} {path}"
            url = "{{{{baseUrl}}}}" + path
            request: Dict[str, Any] = {
                "name": req_name,
                "request": {
                    "method": method.upper(),
                    "header": [
                        {"key": "Content-Type", "value": "application/json"}
                    ],
                    "url": {"raw": url, "host": ["{{baseUrl}}"], "path": path.strip("/").split("/")},
                },
            }
            # For POST-like, include empty body schema as example
            if method.upper() in ("POST", "PUT", "PATCH"):
                request["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("example", {}), indent=2)
                }
            folder["item"].append(request)
        collection["item"].append(folder)
    return collection


def main() -> int:
    try:
        spec = load_openapi(OPENAPI_PATH)
    except FileNotFoundError:
        print(f"ERROR: Spec not found at {OPENAPI_PATH}")
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    col = as_postman(spec)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(col, f, indent=2)
    print(f"Wrote Postman collection: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
