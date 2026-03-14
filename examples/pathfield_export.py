"""
Partfield export example.

Creates a minimal ISOXML v4 task data containing a single partfield with a
boundary polygon and a planned task referencing it. Writes to a ZIP archive.

Usage:
    python examples/pathfield_export.py
"""

from pathlib import Path

import shapely as shp

import isoxml.models.base.v4 as iso
from isoxml.geometry import ShapelyConverterV4
from isoxml.io import write_to_zip

BASE_DIR = Path(__file__).parent
OUTPUT_PATH = BASE_DIR / "output" / "example_partfield.zip"

FIELD_WKT = (
    "POLYGON((15.1447424 48.1255056, 15.1474165 48.1261199, 15.1473747 48.1262158, "
    "15.1482940 48.1263951, 15.1483067 48.1264138, 15.1482915 48.1264792, "
    "15.1482606 48.1265468, 15.1482752 48.1265771, 15.1482575 48.1266392, "
    "15.1481435 48.1267167, 15.1479174 48.1268654, 15.1476676 48.1270070, "
    "15.1475497 48.1270453, 15.1473535 48.1271016, 15.1470970 48.1271263, "
    "15.1461062 48.1271846, 15.1451041 48.1274747, 15.1445809 48.1272868, "
    "15.1441020 48.1270989, 15.1446598 48.1260670, 15.1447174 48.1259533, "
    "15.1447382 48.1258014, 15.1447195 48.1257321, 15.1447079 48.1255547, "
    "15.1447418 48.1255612, 15.1447424 48.1255056))"
)

converter = ShapelyConverterV4()


def main() -> None:
    boundary = converter.to_iso_polygon(
        shp.from_wkt(FIELD_WKT), iso.PolygonType.PartfieldBoundary
    )
    partfield = iso.Partfield(
        id="PFD01",
        designator="test_partfield",
        area=39800,
        polygons=[boundary],
    )
    task = iso.Task(
        id="TSK01",
        partfield_id_ref=partfield.id,
        status=iso.TaskStatus.Running,
    )
    task_data = iso.Iso11783TaskData(
        management_software_manufacturer="josephinum research",
        management_software_version="0.0.1",
        data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
        partfields=[partfield],
        tasks=[task],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        write_to_zip(f, task_data)
    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
