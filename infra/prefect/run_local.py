from __future__ import annotations

"""Optional local runner that reads schedules.yaml and triggers flows.
This is not a full Prefect deployment—just a convenience for dev.
"""

import yaml
import subprocess
from pathlib import Path

SCHEDULES = Path(__file__).resolve().parent / "schedules.yaml"


def run():
    data = yaml.safe_load(SCHEDULES.read_text(encoding="utf-8"))
    # naive: run each target once, in a blocking fashion
    print("Running RSS -> Meili/Qdrant index")
    subprocess.run(["python", str(Path.cwd() / "flows" / "ingest_rss.py")], check=False)
    print("Running EDGAR")
    subprocess.run(["python", str(Path.cwd() / "flows" / "ingest_edgar.py")], check=False)
    print("Running GitHub")
    subprocess.run(["python", str(Path.cwd() / "flows" / "ingest_github.py")], check=False)
    print("Running Graph Sync")
    subprocess.run(["python", str(Path.cwd() / "flows" / "graph_sync.py")], check=False)


if __name__ == "__main__":
    run()
