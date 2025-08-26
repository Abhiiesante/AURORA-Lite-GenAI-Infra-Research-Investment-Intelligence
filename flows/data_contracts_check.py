import json
import os
import sys
from typing import Tuple

# Optional dependency flags (import lazily inside functions)
GE_AVAILABLE = False
try:
    import importlib
    importlib.import_module("great_expectations")
    GE_AVAILABLE = True
except Exception:
    GE_AVAILABLE = False


DATA_DIR = os.getenv("DATA_DIR", "data/raw")


def validate_parquet(name: str, path: str, schema_path: str) -> Tuple[str, bool]:
    import pandas as pd
    if not os.path.exists(path):
        return (f"{name}: missing parquet {path}", False)
    df = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_json(path)
    if not GE_AVAILABLE:
        # Fallback: basic required columns check against JSON schema
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        props = schema["items"]["properties"]
        required = schema["items"].get("required", [])
        missing_cols = [c for c in required if c not in df.columns]
        if missing_cols:
            return (f"{name}: missing required columns {missing_cols}", False)
        return (f"{name}: basic schema check passed ({len(df)} rows)", True)

    # GE path (lightweight)
    from great_expectations.dataset import PandasDataset  # type: ignore
    class DS(PandasDataset):  # type: ignore
        pass  # noqa: E701

    ds = DS(df)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    required = schema["items"].get("required", [])
    failures = []
    for col in required:
        r = ds.expect_column_to_exist(col)
        if not r["success"]:
            failures.append(col)
    if failures:
        return (f"{name}: missing required columns {failures}", False)
    return (f"{name}: GE checks passed ({len(df)} rows)", True)


def main():
    checks = [
        ("news_items", os.path.join("data", "raw", "news_items.parquet"), os.path.join("db", "schemas", "news_items.schema.json")),
        ("filings", os.path.join("data", "raw", "filings.parquet"), os.path.join("db", "schemas", "filings.schema.json")),
        ("repos", os.path.join("data", "raw", "repos.parquet"), os.path.join("db", "schemas", "repos.schema.json")),
    ]
    messages = []
    ok = True
    for name, path, schema in checks:
        msg, success = validate_parquet(name, path, schema)
        messages.append(msg)
        ok = ok and success
    print("\n".join(messages))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
