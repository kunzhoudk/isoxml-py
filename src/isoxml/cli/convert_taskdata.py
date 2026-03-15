"""CLI for converting ISOXML task-data packages."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from isoxml.cli._common import load_taskdata_bundle, write_taskdata_bundle
from isoxml.pipeline import convert_taskdata_versions


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert ISOXML task-data grids between XML versions and grid types."
    )
    parser.add_argument("source", type=Path, help="Input ISOXML folder or ZIP archive.")
    parser.add_argument("--target-xml-version", required=True, choices=["3", "4"])
    parser.add_argument("--target-grid-type", required=True, choices=["1", "2"])
    parser.add_argument(
        "--output-dir", type=Path, help="Write converted files to a directory."
    )
    parser.add_argument(
        "--output-zip", type=Path, help="Write converted files to a ZIP archive."
    )
    parser.add_argument(
        "--skip-xsd-validation",
        action="store_true",
        help="Skip XSD validation after conversion.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    task_data, refs = load_taskdata_bundle(args.source)

    result = convert_taskdata_versions(
        task_data,
        refs,
        target_xml_version=args.target_xml_version,
        target_grid_type=args.target_grid_type,
        validate_output=not args.skip_xsd_validation,
    )

    write_taskdata_bundle(
        result.task_data,
        result.refs,
        output_dir=args.output_dir,
        output_zip=args.output_zip,
        require_exactly_one=True,
    )

    if result.validated_xsd_path is not None:
        print(f"XSD validation: OK ({result.validated_xsd_path.name})")


if __name__ == "__main__":
    main()
