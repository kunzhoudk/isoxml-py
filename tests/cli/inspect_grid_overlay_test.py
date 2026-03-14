from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "isoxml.cli.inspect_grid_overlay", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_help__when_invoked__expect_expected_arguments_visible():
    proc = _run_cli("--help")
    assert "--task-index" in proc.stdout
    assert "--grid-index" in proc.stdout
    assert "--show-zero" in proc.stdout
