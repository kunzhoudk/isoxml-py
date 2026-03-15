"""CLI for validating ISOXML TaskData against bundled XSD schemas."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from isoxml.cli._common import load_taskdata
from isoxml.xsd_validation import validate_xsd


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

def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    task_data = load_taskdata(args.source, read_bin_files=False)
    xsd_path = validate_xsd(task_data, xml_version=args.xml_version)
    print(f"XSD validation: OK ({xsd_path.name})")


if __name__ == "__main__":
    main()
