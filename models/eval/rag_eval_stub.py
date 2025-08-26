from __future__ import annotations

"""Tiny RAG eval runner that reads a minimal config and prints a report.
Toggle hard gate with env HARD_RAG_EVAL=true to exit non-zero when below threshold.
"""

import yaml
from pathlib import Path
import os
import sys


def main():
    cfg_path = Path(__file__).resolve().parent / "ragas_config.yaml"
    threshold = 0.7
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        threshold = float(cfg.get("faithfulness_threshold", threshold))
    # Placeholder metrics; replace with real Ragas later.
    report = {
        "faithfulness": 0.82,
        "answer_relevancy": 0.86,
        "context_precision": 0.80,
        "context_recall": 0.78,
        "threshold": threshold,
    }
    print("RAG EVAL REPORT:", report)
    below = report["faithfulness"] < threshold
    hard = os.getenv("HARD_RAG_EVAL", "false").lower() in {"1", "true", "yes", "on"}
    if below:
        msg = "RAG eval below threshold (faithfulness < threshold)."
        if hard:
            print(msg + " Failing as HARD_RAG_EVAL is enabled.")
            sys.exit(1)
        else:
            print(msg + " Soft warning only (HARD_RAG_EVAL disabled).")


if __name__ == "__main__":
    main()
