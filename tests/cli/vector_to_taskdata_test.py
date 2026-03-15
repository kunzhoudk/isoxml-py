from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from isoxml.io.reader import read_from_path as isoxml_from_path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "isoxml.cli.vector_to_taskdata", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_help__when_invoked__expect_expected_arguments_visible():
    proc = _run_cli("--help")
    assert "--boundary-path" in proc.stdout
    assert "--grid-type" in proc.stdout
    assert "--value-unit" in proc.stdout


def test_cli_run__when_small_sample_input__expect_outputs_created_and_parseable(
    tmp_path: Path,
):
    output_dir = tmp_path / "taskdata"
    output_zip = tmp_path / "taskdata.zip"

    proc = _run_cli(
        "examples/input/small/shp/Rx.shp",
        "--boundary-path",
        "examples/input/small/boundary/Boundary.shp",
        "--grid-type",
        "1",
        "--value-field",
        "rate",
        "--output-dir",
        str(output_dir),
        "--output-zip",
        str(output_zip),
        "--no-xsd-validate",
    )

    assert "ISOXML conversion complete" in proc.stdout
    assert output_dir.joinpath("TASKDATA.XML").exists()
    assert output_dir.joinpath("GRD00000.bin").exists()
    assert output_zip.exists()

    task_data, refs = isoxml_from_path(output_dir)
    grid = task_data.tasks[0].grids[0]
    assert int(grid.maximum_row) > 0
    assert int(grid.maximum_column) > 0
    assert grid.filename in refs


def test_cli_run__when_geojson_with_embedded_boundary__expect_outputs_created_and_parseable(
    tmp_path: Path,
):
    output_dir = tmp_path / "taskdata_geojson"

    proc = _run_cli(
        "examples/input/test_shp_application_map_with_boundary.geojson",
        "--grid-type",
        "1",
        "--xml-version",
        "4",
        "--value-field",
        "dose",
        "--output-dir",
        str(output_dir),
        "--no-xsd-validate",
    )

    assert "ISOXML conversion complete" in proc.stdout
    assert output_dir.joinpath("TASKDATA.XML").exists()
    assert output_dir.joinpath("GRD00000.bin").exists()

    task_data, refs = isoxml_from_path(output_dir)
    grid = task_data.tasks[0].grids[0]
    assert task_data.version_major.value == "4"
    assert int(grid.maximum_row) > 0
    assert int(grid.maximum_column) > 0
    assert grid.filename in refs
