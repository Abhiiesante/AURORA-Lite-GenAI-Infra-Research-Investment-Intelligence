import json
from pathlib import Path
from fastapi.testclient import TestClient

import aurora.main as main


def test_evals_summary_not_below_baseline_by_5_percent():
    client = TestClient(main.app)
    resp = client.get("/evals/summary")
    assert resp.status_code == 200
    current = resp.json()

    baseline_path = Path(__file__).parent / "data" / "evals_baseline.json"
    assert baseline_path.exists(), "baseline file missing"
    baseline = json.loads(baseline_path.read_text())

    def below_threshold(curr: float, base: float) -> bool:
        # Fail if the current drops by more than 5% from baseline
        return curr < (base * 0.95)

    for k in ["faithfulness", "relevancy", "recall"]:
        assert k in current, f"missing metric {k} in current summary"
        assert k in baseline, f"missing metric {k} in baseline summary"
        assert not below_threshold(current[k], baseline[k]), f"{k} dipped more than 5%: {current[k]} < 0.95*{baseline[k]}"
