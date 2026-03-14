"""CLI for validating ISOXML TaskData against bundled XSD schemas."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from isoxml.io import read_from_path, read_from_zip
from isoxml.validation import validate_xsd


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ISOXML TaskData against the bundled XSD.")
    parser.add_argument("source", type=Path, help="TASKDATA directory, XML file, or ZIP archive.")
    parser.add_argument(
        "--xml-version",
        choices=["3", "4"],
        default=None,
        help="Override the XML version used for XSD selection.",
    )
    return parser.parse_args(argv)


def _load_task_data(source: Path):
    if source.suffix.lower() == ".zip":
        task_data, _ = read_from_zip(source, read_bin_files=False)
        return task_data
    task_data, _ = read_from_path(source, read_bin_files=False)
    return task_data


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    task_data = _load_task_data(args.source)
    xsd_path = validate_xsd(task_data, xml_version=args.xml_version)
    print(f"XSD validation: OK ({xsd_path.name})")


if __name__ == "__main__":
    main()
