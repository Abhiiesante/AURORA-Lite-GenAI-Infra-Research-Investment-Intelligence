import sys, time
import requests

BASE = "http://127.0.0.1:3000/market-map"

def main():
    # wait a bit for dev server in CI-ish runs
    for i in range(10):
        try:
            r = requests.get(BASE, timeout=5)
            if r.status_code == 200 and ("Use KG source" in r.text or "KG mode" in r.text):
                print("OK: Market Map page loaded and contains KG toggle text")
                return 0
            # also verify KG mode via URL
            r2 = requests.get(BASE + "?source=kg", timeout=5)
            if r2.status_code == 200 and ("KG mode" in r2.text or "Use KG source" in r2.text):
                print("OK: Market Map source=kg responds with page and KG indicators")
                return 0
        except Exception:
            time.sleep(1)
            continue
        time.sleep(1)
    print("FAIL: Market Map page did not load or lacked expected text")
    return 1

if __name__ == "__main__":
    sys.exit(main())
