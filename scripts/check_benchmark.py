"""Sanity check of the benchmark.

For every task we check two things, each in a temporary copy of the repo:
  1. the tests FAIL on the buggy code (otherwise there is nothing to fix);
  2. the tests PASS once the reference fix is applied (otherwise the task
     is impossible, or the tests are wrong).

Usage:
    python scripts/check_benchmark.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "benchmark"


def tests_pass(repo_dir):
    """Run pytest in `repo_dir` and return True if every test passes."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode == 0


all_ok = True
for task in sorted(p for p in BENCHMARK_DIR.iterdir() if p.is_dir()):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(task / "repo", work)
        buggy_passes = tests_pass(work)

        # Overwrite the buggy files with the fixed ones.
        for fixed_file in (task / "fix").iterdir():
            shutil.copy(fixed_file, work / fixed_file.name)
        fixed_passes = tests_pass(work)

    ok = not buggy_passes and fixed_passes
    all_ok = all_ok and ok
    print(
        f"{task.name:15s} | buggy: {'pass' if buggy_passes else 'FAIL'}"
        f" | fixed: {'pass' if fixed_passes else 'FAIL'} | {'OK' if ok else 'BROKEN'}"
    )

print("\nBenchmark is valid." if all_ok else "\nSome tasks are broken!")
sys.exit(0 if all_ok else 1)
