from decimal import Decimal

import pytest

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.geometry import ShapelyConverterV3


def test__to_shapely_polygon__when_shell_missing__expect_error():
    converter = ShapelyConverterV3()
    iso_polygon = iso3.Polygon(
        type=iso3.PolygonType.Other,
        line_strings=[
            iso3.LineString(
                type=iso3.LineStringType.PolygonInterior,
                points=[
                    iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(0)),
                    iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(1)),
                    iso3.Point(type=iso3.PointType.Other, north=Decimal(1), east=Decimal(0)),
                    iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(0)),
                ],
            )
        ],
    )

    with pytest.raises(ValueError):
        converter.to_shapely_polygon(iso_polygon)


def test__to_shapely_polygon__when_multiple_shells__expect_not_implemented():
    converter = ShapelyConverterV3()
    shell_a = iso3.LineString(
        type=iso3.LineStringType.Flag,
        points=[
            iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(0)),
            iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(1)),
        ],
    )
    shell_b = iso3.LineString(
        type=iso3.LineStringType.Flag,
        points=[
            iso3.Point(type=iso3.PointType.Other, north=Decimal(1), east=Decimal(1)),
            iso3.Point(type=iso3.PointType.Other, north=Decimal(1), east=Decimal(2)),
        ],
    )
    iso_polygon = iso3.Polygon(type=iso3.PolygonType.Other, line_strings=[shell_a, shell_b])

    with pytest.raises(NotImplementedError):
        converter.to_shapely_polygon(iso_polygon)


def test__to_shapely_geom__when_geometry_from_other_version__expect_not_implemented():
    converter = ShapelyConverterV3()
    iso_point_v4 = iso4.Point(type=iso4.PointType.Flag, north=Decimal(1), east=Decimal(2))

    with pytest.raises(NotImplementedError):
        converter.to_shapely_geom(iso_point_v4)
