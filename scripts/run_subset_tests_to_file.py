import sys
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp" / "last_test_output.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

TESTS = [
    str(ROOT / "apps" / "api" / "tests" / "test_m3_people_investor_endpoints.py"),
    str(ROOT / "apps" / "api" / "tests" / "test_m3_deals_forecast_endpoints.py"),
]

class Capture:
    def __init__(self):
        self.lines = []
    def write(self, s):
        self.lines.append(s)
    def flush(self):
        pass

cap = Capture()
ret = pytest.main(TESTS)

with OUT.open("w", encoding="utf-8") as f:
    f.write("exit_code=" + str(ret) + "\n")

print(str(OUT))
