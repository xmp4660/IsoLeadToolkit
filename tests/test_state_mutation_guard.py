"""Ensure app_state direct assignment guard remains green."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path



def test_state_mutation_guard_script_reports_zero_hits() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "check_state_mutations.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--fail-on-hits"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "TOTAL=0" in result.stdout
