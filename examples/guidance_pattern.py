"""
Guidance pattern example.

Creates an ISOXML v4 partfield with two guidance patterns:
  - AB line: straight guidance between two reference points
  - Curve: free-form guidance with point-by-point geometry

Output is written to examples/output/example_guidance/TASKDATA.XML.

Usage:
    python examples/guidance_pattern.py
"""

from importlib import resources
from pathlib import Path

import shapely as shp

import isoxml.models.base.v4 as iso
from isoxml.geometry import ShapelyConverterV4
from isoxml.io import write_to_dir

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output" / "example_guidance"

SWATHE_WIDTH = 3000  # mm

AB_WKT = "LINESTRING (15.1472554 48.1263457, 15.1470881 48.1264582)"
CURVE_WKT = (
    "LINESTRING (15.1452147 48.1259334, 15.1456092 48.1260317, 15.1459001 48.1260745, "
    "15.1459019 48.1260748, 15.1459037 48.1260753, 15.1459053 48.1260758, "
    "15.1464337 48.1262656, 15.1464345 48.1262658, 15.1468234 48.1264198, "
    "15.1468253 48.1264207, 15.1468271 48.1264217, 15.1471490 48.1266280)"
)
BOUNDARY_WKT = (
    "POLYGON((15.1450455 48.1257726, 15.1455444 48.1255685, 15.1461560 48.1256759, "
    "15.1466280 48.1259194, 15.1476044 48.1263777, 15.1471484 48.1266463, "
    "15.1468131 48.1264314, 15.1464242 48.1262775, 15.1458958 48.1260877, "
    "15.1456034 48.1260447, 15.1452011 48.1259445, 15.1450455 48.1257726))"
)

converter = ShapelyConverterV4()


def build_ab_pattern() -> iso.GuidancePattern:
    line = converter.to_iso_line_string(shp.from_wkt(AB_WKT), iso.LineStringType.GuidancePattern)
    line.points[0].type = iso.PointType.GuidanceReferenceA
    line.points[1].type = iso.PointType.GuidanceReferenceB
    line.width = SWATHE_WIDTH
    return iso.GuidancePattern(
        id="GPN01",
        type=iso.GuidancePatternType.AB,
        designator="AB guidance pattern",
        line_strings=[line],
        propagation_direction=iso.GuidancePatternPropagationDirection.LeftDirectionOnly,
        extension=iso.GuidancePatternExtension.FromBothFirstAndLastPoint,
        number_of_swaths_left=10,
        number_of_swaths_right=0,
    )


def build_curve_pattern() -> iso.GuidancePattern:
    line = converter.to_iso_line_string(shp.from_wkt(CURVE_WKT), iso.LineStringType.GuidancePattern)
    for point in line.points:
        point.type = iso.PointType.GuidancePoint
    line.points[0].type = iso.PointType.GuidanceReferenceA
    line.points[-1].type = iso.PointType.GuidanceReferenceB
    line.width = SWATHE_WIDTH
    return iso.GuidancePattern(
        id="GPN02",
        type=iso.GuidancePatternType.Curve,
        designator="curve guidance pattern",
        line_strings=[line],
        propagation_direction=iso.GuidancePatternPropagationDirection.RightDirectionOnly,
        extension=iso.GuidancePatternExtension.NoExtensions,
        number_of_swaths_left=0,
        number_of_swaths_right=4,
    )


def main() -> None:
    boundary = converter.to_iso_polygon(
        shp.from_wkt(BOUNDARY_WKT), iso.PolygonType.PartfieldBoundary
    )
    customer = iso.Customer(id="CTR101", last_name="jr_customer")
    farm = iso.Farm(id="FRM101", designator="jr_farm", customer_id_ref=customer.id)

    partfield = iso.Partfield(
        id="PFD01",
        designator="test_partfield",
        area=1050,
        polygons=[boundary],
        guidance_groups=[
            iso.GuidanceGroup(
                id="GGP01",
                designator="test_guidance_group",
                guidance_patterns=[build_ab_pattern(), build_curve_pattern()],
            )
        ],
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
    )

    task_data = iso.Iso11783TaskData(
        management_software_manufacturer="josephinum research",
        management_software_version="0.0.1",
        data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_to_dir(OUTPUT_DIR, task_data)

    try:
        import xmlschema
        xsd_ref = resources.files("isoxml.data.xsd").joinpath("ISO11783_TaskFile_V4-3.xsd")
        with resources.as_file(xsd_ref) as xsd_path:
            xmlschema.validate(OUTPUT_DIR / "TASKDATA.XML", xsd_path)
        print("XSD validation: OK")
    except ImportError:
        print("Install xmlschema to enable XSD validation.")

    print(f"Written: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
