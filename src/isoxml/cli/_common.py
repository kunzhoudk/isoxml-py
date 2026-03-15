"""Shared helpers for CLI entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from isoxml.io import read_from_path, read_from_zip, write_to_dir, write_to_zip


def load_taskdata_bundle(
    source: Path,
    *,
    read_bin_files: bool = True,
) -> tuple[Any, dict[str, object]]:
    """Load ISOXML task data and references from a directory, XML file, or ZIP archive."""
    if source.suffix.lower() == ".zip":
        return read_from_zip(source, read_bin_files=read_bin_files)
    return read_from_path(source, read_bin_files=read_bin_files)


def load_taskdata(source: Path, *, read_bin_files: bool = False) -> Any:
    """Load only the task-data root object from a supported source."""
    task_data, _ = load_taskdata_bundle(source, read_bin_files=read_bin_files)
    return task_data


def write_taskdata_bundle(
    task_data: Any,
    refs: dict[str, object],
    *,
    output_dir: Path | None = None,
    output_zip: Path | None = None,
    require_exactly_one: bool = False,
) -> None:
    """Write task data to a directory, ZIP archive, or both."""
    if require_exactly_one and bool(output_dir) == bool(output_zip):
        raise SystemExit("Specify exactly one of --output-dir or --output-zip.")
    if output_dir is None and output_zip is None:
        raise SystemExit("Specify at least one output target.")

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_to_dir(output_dir, task_data, refs)
    if output_zip is not None:
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        write_to_zip(output_zip, task_data, refs)


def require_task(task_data: Any, task_index: int) -> Any:
    """Return the requested task or raise a stable index error."""
    if len(task_data.tasks) <= task_index:
        raise IndexError(
            f"Task index {task_index} out of range (found {len(task_data.tasks)})."
        )
    return task_data.tasks[task_index]


def require_grid(task: Any, grid_index: int) -> Any:
    """Return the requested grid or raise a stable index error."""
    if len(task.grids) <= grid_index:
        raise IndexError(
            f"Grid index {grid_index} out of range (found {len(task.grids)})."
        )
    return task.grids[grid_index]


def default_sidecar_path(source: Path, name: str) -> Path:
    """Resolve a sibling output path next to a source directory or archive."""
    return (source / name) if source.is_dir() else source.with_name(name)
