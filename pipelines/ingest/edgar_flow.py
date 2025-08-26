from prefect import flow, task
import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET

DATA_DIR = os.environ.get("DATA_DIR", "/data")
HEADERS = {"User-Agent": "AURORA-Lite/0.1 (student research) contact@example.com"}
RSS_URL = "https://www.sec.gov/Archives/edgar/xbrlrss.all.xml"

@task
def fetch_feed(url: str):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

@task
def parse_and_persist(xml_text: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(DATA_DIR, f"edgar_{ts}.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_text)
    # minimal parse sanity
    try:
        root = ET.fromstring(xml_text)
        count = len(root.findall(".//item"))
    except Exception:
        count = 0
    return {"path": path, "items": count}

@flow
def edgar_flow():
    xml_text = fetch_feed(RSS_URL)
    return parse_and_persist(xml_text)

if __name__ == "__main__":
    print(edgar_flow())
