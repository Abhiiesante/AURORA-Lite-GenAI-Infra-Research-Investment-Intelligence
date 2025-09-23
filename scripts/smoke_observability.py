import sys
import json
import re
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

def main():
    print(f"Checking {BASE} ...")
    r = requests.get(f"{BASE}/metrics")
    r.raise_for_status()
    body = r.text
    assert "# HELP" in body and "aurora_request_latency_avg_ms" in body
    # Presence checks for core gauges/counters (lightweight/non-brittle)
    assert "aurora_requests_total" in body
    # Accept presence of hybrid cache help lines or values; environments may vary
    if not re.search(r"^aurora_hybrid_cache_hits\s+\d+", body, re.M):
        # Still require the HELP/TYPE to exist to catch regressions
        assert "# HELP aurora_hybrid_cache_hits" in body
    print("/metrics OK")

    r = requests.get(f"{BASE}/dev/gates/status?strict=false")
    r.raise_for_status()
    js = r.json()
    assert "pass" in js and "gates" in js
    print("/dev/gates/status OK", json.dumps({"pass": js.get("pass")}))

if __name__ == "__main__":
    main()
