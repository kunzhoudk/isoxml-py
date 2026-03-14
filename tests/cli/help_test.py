from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("module_name", "expected_flag"),
    [
        ("isoxml.cli.inspect_shapefile", "shp_path"),
        ("isoxml.cli.generate_pycode", "--var-name"),
        ("isoxml.cli.validate_taskdata", "--xml-version"),
        ("isoxml.cli.validate_grid_bin", "--value-field"),
        ("isoxml.cli.inspect_grid", "--ddi"),
    ],
)
def test_cli_module_help__when_invoked__expect_expected_flag_visible(
    module_name: str,
    expected_flag: str,
):
    proc = subprocess.run(
        [sys.executable, "-m", module_name, "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert expected_flag in proc.stdout
