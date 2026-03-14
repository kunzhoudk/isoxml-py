"""CLI for converting polygon prescription shapefiles to ISOXML grids."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from isoxml.io import write_to_dir, write_to_zip
from isoxml.pipeline.shp_to_grid import ShpToGridOptions, convert, validate_xsd


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parents[3] / "examples"
    parser = argparse.ArgumentParser(
        description="Convert a polygon prescription shapefile to an ISOXML grid map.",
    )
    parser.add_argument(
        "shp_path",
        nargs="?",
        type=Path,
        default=base_dir / "input" / "small" / "shp" / "Rx.shp",
        help="Prescription shapefile (.shp).",
    )
    parser.add_argument(
        "--boundary-shp",
        type=Path,
        default=None,
        help="Boundary shapefile for partfield geometry.",
    )
    parser.add_argument(
        "--value-field",
        type=str,
        default=None,
        help="Numeric attribute used as prescription value (auto-detected if omitted).",
    )
    parser.add_argument(
        "--ddi",
        type=int,
        default=6,
        help="DDI for grid values (default: 6 = Setpoint Mass Per Area).",
    )
    parser.add_argument(
        "--value-unit",
        choices=["auto", "ddi", "kg/ha"],
        default="auto",
        help="Unit of the value field. 'auto' reads from shapefile; 'ddi' means already in DDI base unit.",
    )
    parser.add_argument(
        "--grid-type",
        choices=["1", "2"],
        default="2",
        help="ISOXML grid type (default: 2).",
    )
    parser.add_argument(
        "--xml-version",
        choices=["3", "4"],
        default="3",
        help="ISOXML version to generate (default: 3).",
    )
    parser.add_argument(
        "--cell-size-m",
        type=float,
        default=10.0,
        help="Grid cell size in metres (default: 10).",
    )
    parser.add_argument(
        "--boundary-mask",
        choices=["center", "strict", "touch"],
        default="touch",
        help="Cell masking strategy against boundary (default: touch).",
    )
    parser.add_argument(
        "--grid-extent",
        choices=["rx", "boundary", "union"],
        default="rx",
        help="Bounding box source for grid origin/size (default: rx).",
    )
    parser.add_argument(
        "--input-crs",
        type=str,
        default=None,
        help="CRS to apply when input has no CRS metadata, e.g. EPSG:4326.",
    )
    parser.add_argument(
        "--partfield-name",
        type=str,
        default=None,
        help="Partfield designator (default: auto-detected from file).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "output" / "rx_grid",
        help="Output directory for TASKDATA.XML and GRD*.bin.",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=None,
        help="Optional ZIP output path.",
    )
    parser.add_argument(
        "--software-manufacturer",
        type=str,
        default="isoxml-py",
    )
    parser.add_argument(
        "--software-version",
        type=str,
        default="0.1.0",
    )
    parser.add_argument(
        "--no-xsd-validate",
        action="store_true",
        help="Skip XSD validation after generation.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    options = ShpToGridOptions(
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

    result = convert(options)

    if not args.no_xsd_validate:
        xsd_path = validate_xsd(result.task_data, args.xml_version)
        print(f"  xsd: OK ({xsd_path.name})")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_to_dir(args.output_dir, result.task_data, result.refs)

    if args.output_zip is not None:
        args.output_zip.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_zip, "wb") as file_handle:
            write_to_zip(file_handle, result.task_data, result.refs)

    grid = result.task_data.tasks[0].grids[0]
    print("ISOXML conversion complete")
    print(f"  input:       {args.shp_path}")
    print(f"  boundary:    {args.boundary_shp}")
    print(f"  xml version: {args.xml_version}")
    print(f"  grid type:   {args.grid_type}")
    print(f"  value field: {result.value_field}")
    print(f"  value unit:  {result.effective_unit} (source: {result.unit_source})")
    print(f"  grid size:   {grid.maximum_row} rows x {grid.maximum_column} cols")
    print(f"  zones:       {len(result.task_data.tasks[0].treatment_zones)}")
    print(f"  output dir:  {args.output_dir}")
    if args.output_zip is not None:
        print(f"  output zip:  {args.output_zip}")


if __name__ == "__main__":
    main()
