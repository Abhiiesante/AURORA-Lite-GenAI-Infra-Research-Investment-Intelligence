from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_people_graph_shape():
    c = TestClient(app)
    r = c.get("/people/graph/1")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data and isinstance(data["nodes"], list)
    assert "edges" in data and isinstance(data["edges"], list)


def test_investor_profile_and_syndicates_and_playbook():
    c = TestClient(app)
    prof = c.get("/investors/profile/a16z").json()
    syn = c.get("/investors/syndicates/a16z").json()
    pb = c.get("/playbook/investor/a16z", params={"company": "Pinecone"}).json()

    assert prof.get("id") or prof.get("name")
    assert syn.get("investor") == "a16z"
    assert isinstance(syn.get("syndicates"), list)
    assert pb.get("investor") is not None
    assert isinstance(pb.get("recommended_pitch"), str)
