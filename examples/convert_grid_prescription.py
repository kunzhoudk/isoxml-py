"""Convert ISOXML prescription packages across XML versions and grid types.

Examples:
    python examples/convert_grid_prescription.py tests/resources/isoxml/v3/grid_type_2 \
        --target-xml-version 4 --target-grid-type 1 --output-dir /tmp/isoxml_out
"""

from __future__ import annotations

import argparse
from pathlib import Path

from isoxml.io import read_from_path, read_from_zip, write_to_dir, write_to_zip
from isoxml.pipeline import convert_grid_prescriptions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert ISOXML prescription grids between XML versions and grid types."
    )
    parser.add_argument("source", type=Path, help="Input ISOXML folder or ZIP archive.")
    parser.add_argument("--target-xml-version", required=True, choices=["3", "4"])
    parser.add_argument("--target-grid-type", required=True, choices=["1", "2"])
    parser.add_argument("--output-dir", type=Path, help="Write converted files to a directory.")
    parser.add_argument("--output-zip", type=Path, help="Write converted files to a ZIP archive.")
    parser.add_argument(
        "--skip-xsd-validation",
        action="store_true",
        help="Skip XSD validation after conversion.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.output_dir) == bool(args.output_zip):
        raise SystemExit("Specify exactly one of --output-dir or --output-zip.")

    if args.source.suffix.lower() == ".zip":
        task_data, refs = read_from_zip(args.source)
    else:
        task_data, refs = read_from_path(args.source)

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=args.target_xml_version,
        target_grid_type=args.target_grid_type,
        validate_output=not args.skip_xsd_validation,
    )

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_to_dir(args.output_dir, result.task_data, result.refs)
    else:
        write_to_zip(args.output_zip, result.task_data, result.refs)

    if result.validated_xsd_path is not None:
        print(f"XSD validation: OK ({result.validated_xsd_path.name})")


if __name__ == "__main__":
    main()
