import json
from pathlib import Path
from fastapi.testclient import TestClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.aurora.main import app

client = TestClient(app)

endpoints = [
    ("people_graph", "/people/graph/1", {}),
    ("investor_profile", "/investors/profile/a16z", {}),
    ("investor_syndicates", "/investors/syndicates/a16z", {}),
    ("playbook", "/playbook/investor/a16z", {"company": "Pinecone"}),
    ("deals", "/deals/sourcing", {"limit": 5}),
    ("forecast", "/forecast/1", {"metric": "mentions", "horizon": 4}),
]

results = {}
for name, path, params in endpoints:
    r = client.get(path, params=params)
    results[name] = {
        "status": r.status_code,
        "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text,
    }

out_path = Path(__file__).resolve().parents[1] / "tmp" / "diag_endpoints.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(str(out_path))
