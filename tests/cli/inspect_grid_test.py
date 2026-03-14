from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "resources" / "isoxml" / "prescription_converter"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "isoxml.cli.inspect_grid", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_inspect_grid_cli_run__when_type2_fixture__expect_stats_and_csv_output(tmp_path: Path):
    source_zip = tmp_path / "small_xml_v3_type_2_auto.zip"
    shutil.copy2(FIXTURE_DIR / "small_xml_v3_type_2_auto.zip", source_zip)

    proc = _run_cli(str(source_zip), "--ddi", "6")

    assert "Grid metadata" in proc.stdout
    assert "Decoded array" in proc.stdout
    assert "DDI: 0006" in proc.stdout
    assert "CSV written:" in proc.stdout
    assert tmp_path.joinpath("GRD00000.csv").exists()


def test_inspect_grid_cli_run__when_type1_fixture__expect_zone_code_mode_and_csv_output(
    tmp_path: Path,
):
    source_zip = tmp_path / "small_xml_v3_type_1_auto.zip"
    shutil.copy2(FIXTURE_DIR / "small_xml_v3_type_1_auto.zip", source_zip)

    proc = _run_cli(str(source_zip))

    assert "Grid metadata" in proc.stdout
    assert "Decoded array" in proc.stdout
    assert "mode: zone codes (Grid Type 1)" in proc.stdout
    assert "CSV written:" in proc.stdout
    assert tmp_path.joinpath("GRD00000.csv").exists()
