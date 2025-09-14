from fastapi.testclient import TestClient
from apps.api.aurora.main import app

client = TestClient(app)

print("POST /copilot/ask ...", end=" ")
r = client.post("/copilot/ask", json={"question": "qdrant traction"})
print(r.status_code, r.json())

print("GET /metrics ...", end=" ")
r = client.get("/metrics")
print(r.status_code, "len=", len(r.text))

print("POST /compare ...", end=" ")
r = client.post("/compare", json={"companies": ["A","B"], "metrics": ["m1","m2"]})
print(r.status_code, r.json().keys())

print("GET /compare ...", end=" ")
r = client.get("/compare", params=[("companies","A"),("companies","B"),("metric","m1")])
print(r.status_code, r.json().keys())
