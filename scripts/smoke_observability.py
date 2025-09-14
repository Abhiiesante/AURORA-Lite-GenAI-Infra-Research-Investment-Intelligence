import sys
import json
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

def main():
    print(f"Checking {BASE} ...")
    r = requests.get(f"{BASE}/metrics")
    r.raise_for_status()
    assert "# HELP" in r.text and "aurora_request_latency_avg_ms" in r.text
    print("/metrics OK")

    r = requests.get(f"{BASE}/dev/gates/status?strict=false")
    r.raise_for_status()
    js = r.json()
    assert "pass" in js and "gates" in js
    print("/dev/gates/status OK", json.dumps({"pass": js.get("pass")}))

if __name__ == "__main__":
    main()
