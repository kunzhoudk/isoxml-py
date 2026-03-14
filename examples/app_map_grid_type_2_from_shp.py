"""
Convert a polygon prescription shapefile to ISOXML v3 grid map (TASKDATA.XML + GRDxxxx.bin).

Example:
    .venv/bin/python examples/app_map_grid_type_2_from_shp.py \
        examples/input/Rx/Rx.shp \
        --grid-type 1 \
        --value-field rate \
        --cell-size-m 10 \
        --output-dir examples/output/app_map_grid_type_2_from_shp
"""

from __future__ import annotations

import argparse
from pathlib import Path

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4
from isoxml.io import write_to_dir, write_to_zip
from isoxml.pipeline.shp_to_grid import (
    ShpToGridOptions,
    convert,
    validate_xsd,
)


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description="Convert polygon .shp prescription map to ISOXML v3 grid type 1 or 2.",
    )
    parser.add_argument(
        "shp_path",
        nargs="?",
        type=Path,
        default=base_dir / "input" / "Rx" / "Rx.shp",
        help="Input shapefile (.shp).",
    )
    parser.add_argument(
        "--value-field",
        type=str,
        default=None,
        help="Numeric field used as prescription value (auto-detected if omitted).",
    )
    parser.add_argument(
        "--ddi",
        type=int,
        default=6,
        help="DDI used for grid values (default: 6, Setpoint Mass Per Area Application Rate).",
    )
    parser.add_argument(
        "--value-unit",
        choices=["auto", "ddi", "kg/ha"],
        default="auto",
        help=(
            "Unit of input value field. 'auto' tries to read from shapefile fields, "
            "'ddi' means already in DDI base unit, 'kg/ha' will be converted."
        ),
    )
    parser.add_argument(
        "--grid-type",
        choices=["1", "2"],
        default="2",
        help="ISOXML grid type (1=lookup table in XML, 2=values in BIN). Default: 2.",
    )
    parser.add_argument(
        "--xml-version",
        choices=["3", "4"],
        default="3",
        help="ISOXML task data version to generate (default: 3).",
    )
    parser.add_argument(
        "--cell-size-m",
        type=float,
        default=10.0,
        help="Grid cell size in meters in projected CRS (default: 10).",
    )
    parser.add_argument(
        "--boundary-mask",
        choices=["center", "strict", "touch"],
        default="touch",
        help=(
            "Boundary masking strategy. 'center' keeps cells whose center is inside boundary; "
            "'strict' keeps only cells fully covered by boundary; "
            "'touch' keeps cells whose area intersects both polygon and boundary."
        ),
    )
    parser.add_argument(
        "--grid-extent",
        choices=["rx", "boundary", "union"],
        default="rx",
        help=(
            "Bounding box source for grid rows/columns and XML grid origin/size: "
            "'rx' (prescription polygons), 'boundary' (partfield boundary), "
            "'union' (combined extent)."
        ),
    )
    parser.add_argument(
        "--input-crs",
        type=str,
        default=None,
        help="CRS to apply when input file has no CRS metadata, e.g. EPSG:4326.",
    )
    parser.add_argument(
        "--partfield-name",
        type=str,
        default=None,
        help="Partfield designator (default: auto from data/file name).",
    )
    parser.add_argument(
        "--boundary-shp",
        type=Path,
        default=None,
        help="Boundary shapefile (.shp) used to build PFD geometry (required).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "output" / "app_map_grid_type_2_from_shp",
        help="Directory to write TASKDATA.XML and GRD00000.bin.",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=None,
        help="Optional zip output path (e.g. examples/output/app_map_grid_type_2_from_shp.zip).",
    )
    parser.add_argument(
        "--software-manufacturer",
        type=str,
        default="isoxml-py",
        help="ISOXML ManagementSoftwareManufacturer field.",
    )
    parser.add_argument(
        "--software-version",
        type=str,
        default="0.1.0",
        help="ISOXML ManagementSoftwareVersion field.",
    )
    parser.add_argument(
        "--no-xsd-validate",
        action="store_true",
        help="Skip XSD validation after generating TASKDATA.",
    )
    return parser.parse_args()


def _options_from_args(args: argparse.Namespace) -> ShpToGridOptions:
    return ShpToGridOptions(
        shp_path=args.shp_path,
        value_field=args.value_field,
        ddi=args.ddi,
        value_unit=args.value_unit,
        grid_type=args.grid_type,
        xml_version=args.xml_version,
        cell_size_m=args.cell_size_m,
        boundary_mask=args.boundary_mask,
        grid_extent=args.grid_extent,
        input_crs=args.input_crs,
        partfield_name=args.partfield_name,
        boundary_shp=args.boundary_shp,
        software_manufacturer=args.software_manufacturer,
        software_version=args.software_version,
    )


def _validate_taskdata_xsd(
    task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData, xml_version: str
) -> Path:
    return validate_xsd(task_data, xml_version)


def build_isoxml_from_shp(
    args: argparse.Namespace,
) -> tuple[
    iso.Iso11783TaskData | iso4.Iso11783TaskData, dict[str, bytes], str, str, str
]:
    result = convert(_options_from_args(args))
    return (
        result.task_data,
        result.refs,
        result.value_field,
        result.effective_unit,
        result.unit_source,
    )


def main() -> None:
    args = parse_args()
    task_data, refs, value_field, effective_unit, unit_source = build_isoxml_from_shp(
        args
    )

    validated_xsd_path = None
    if not args.no_xsd_validate:
        validated_xsd_path = _validate_taskdata_xsd(task_data, args.xml_version)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_to_dir(output_dir, task_data, refs)

    if args.output_zip is not None:
        args.output_zip.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_zip, "wb") as zip_file:
            write_to_zip(zip_file, task_data, refs)

    grid = task_data.tasks[0].grids[0]
    print("ISOXML conversion complete:")
    print(f"  xml version:{args.xml_version}")
    print(f"  input:      {args.shp_path}")
    print(f"  boundary:   {args.boundary_shp}")
    print(f"  grid type:  {args.grid_type}")
    print(f"  bmask:      {args.boundary_mask}")
    print(f"  gextent:    {args.grid_extent}")
    print(f"  value field:{value_field}")
    print(f"  value unit: {effective_unit} (source: {unit_source})")
    print(f"  grid:       {grid.maximum_row} x {grid.maximum_column}")
    print(f"  zones:      {len(task_data.tasks[0].treatment_zones)}")
    if validated_xsd_path is not None:
        print(f"  xsd:        OK ({validated_xsd_path.name})")
    print(f"  output dir: {output_dir}")
    if args.output_zip is not None:
        print(f"  output zip: {args.output_zip}")


if __name__ == "__main__":
    main()

