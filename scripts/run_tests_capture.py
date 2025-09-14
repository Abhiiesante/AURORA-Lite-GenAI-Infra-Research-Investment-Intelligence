import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run the entire API test suite to validate Phase 3 stability end-to-end
tests_dir = str(ROOT / "apps" / "api" / "tests")
cmd = [sys.executable, "-m", "pytest", tests_dir, "-q"]
proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
outdir = ROOT / "tmp"
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "subset_stdout.txt").write_text(proc.stdout, encoding="utf-8")
(outdir / "subset_stderr.txt").write_text(proc.stderr, encoding="utf-8")
(outdir / "subset_exit.txt").write_text(str(proc.returncode), encoding="utf-8")
print("stdout:", (outdir / "subset_stdout.txt").as_posix())
print("stderr:", (outdir / "subset_stderr.txt").as_posix())
print("exit:", (outdir / "subset_exit.txt").as_posix())
