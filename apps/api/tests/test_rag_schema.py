from __future__ import annotations

from aurora.rag_models import coerce_company_brief_json


def test_coerce_valid():
    obj = {
        "company": "ExampleAI",
        "summary": "Example summary",
        "five_forces": {
            "rivalry": "medium [source: https://example.ai]",
            "new_entrants": "low [source: https://example.ai]",
            "supplier_power": "low [source: https://example.ai]",
            "buyer_power": "medium [source: https://example.ai]",
            "substitutes": "medium [source: https://example.ai]",
        },
        "theses": [
            {
                "statement": "Winning in developer experience",
                "confidence": 0.7,
                "evidence": [{"source": "https://example.ai", "snippet": "..."}],
            }
        ],
    }
    res = coerce_company_brief_json(obj)
    assert res.ok and res.data is not None


def test_coerce_rejects_empty_evidence():
    obj = {
        "company": "ExampleAI",
        "summary": "",
        "five_forces": {
            "rivalry": "low",
            "new_entrants": "low",
            "supplier_power": "low",
            "buyer_power": "low",
            "substitutes": "low",
        },
        "theses": [
            {"statement": "", "confidence": 0.4, "evidence": []}
        ],
    }
    res = coerce_company_brief_json(obj)
    assert not res.ok and res.error
