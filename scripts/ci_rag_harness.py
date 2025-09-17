#!/usr/bin/env python3
import json, sys, os

PATH = os.path.join(os.path.dirname(__file__), '..', 'tests', 'rag_golden_set.json')
PATH = os.path.abspath(PATH)

def main():
    try:
        with open(PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: failed to read golden set: {e}")
        return 1
    if not isinstance(data, list) or not data:
        print("ERROR: golden set must be a non-empty list")
        return 1
    required_top = {"id", "question", "expected_output", "evaluation_rules"}
    ok = True
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"ERROR[{i}]: item is not an object")
            ok = False
            continue
        missing = required_top - set(item.keys())
        if missing:
            print(f"ERROR[{i}]: missing keys: {sorted(missing)}")
            ok = False
        eo = item.get("expected_output", {})
        if not isinstance(eo, dict) or "one_line" not in eo or "evidence" not in eo:
            print(f"ERROR[{i}]: expected_output must have one_line and evidence[]")
            ok = False
        rules = item.get("evaluation_rules", {})
        if not isinstance(rules, dict) or "faithfulness_required" not in rules:
            print(f"ERROR[{i}]: evaluation_rules must include faithfulness_required")
            ok = False
    print("PASS" if ok else "FAIL")
    return 0 if ok else 2

if __name__ == '__main__':
    sys.exit(main())
