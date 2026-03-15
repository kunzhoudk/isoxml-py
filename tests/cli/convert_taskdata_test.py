from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from isoxml.io import read_from_path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT / "tests" / "resources" / "isoxml" / "taskdata_version_converter"
)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "isoxml.cli.convert_taskdata", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_convert_taskdata_cli_run__when_valid_fixture__expect_converted_output_written(
    tmp_path: Path,
):
    output_dir = tmp_path / "converted"

    proc = _run_cli(
        str(FIXTURE_DIR / "small_xml_v3_type_1_auto.zip"),
        "--target-xml-version",
        "4",
        "--target-grid-type",
        "2",
        "--output-dir",
        str(output_dir),
    )

    assert "XSD validation: OK" in proc.stdout
    assert output_dir.joinpath("TASKDATA.XML").exists()
    assert output_dir.joinpath("GRD00000.bin").exists()

    task_data, refs = read_from_path(output_dir)
    grid = task_data.tasks[0].grids[0]

    assert task_data.version_major.value == "4"
    assert int(grid.type.value) == 2
    assert grid.filename in refs
