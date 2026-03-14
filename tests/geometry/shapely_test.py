from decimal import Decimal

import pytest
import shapely as shp

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4
from isoxml.models.base.v4 import Point as PointV4


@pytest.fixture
def v3():
    return ShapelyConverterV3()


@pytest.fixture
def v4():
    return ShapelyConverterV4()


# ---------------------------------------------------------------------------
# Point
# ---------------------------------------------------------------------------

def test_v3_to_iso_point(v3):
    y, x = Decimal('-89.9'), Decimal('179.55')
    iso_pt = v3.to_iso_point(shp.Point(x, y))
    assert isinstance(iso_pt, iso3.Point)
    assert iso_pt.north == y
    assert iso_pt.east == x


def test_v3_to_shapely_point(v3):
    y, x = Decimal(-89.9), Decimal(179.55)
    iso_pt = iso3.Point(type=iso3.PointType.Other, north=y, east=x)
    shp_pt = v3.to_shapely_point(iso_pt)
    assert isinstance(shp_pt, shp.Point)
    assert shp_pt.x == x
    assert shp_pt.y == y


def test_3d_point_truncation(v3):
    iso_pt = v3.to_iso_point(shp.Point(30.5, 10.2, 123.456789))
    assert iso_pt.up == 123456


def test_v4_to_iso_point(v4):
    iso_pt = v4.to_iso_point(shp.Point(179.55, -89.9))
    assert isinstance(iso_pt, PointV4)


def test_v4_to_shapely_point(v4):
    y, x = Decimal(-89.9), Decimal(179.55)
    iso_pt = iso4.Point(type=iso3.PointType.Other, north=y, east=x)
    shp_pt = v4.to_shapely_point(iso_pt)
    assert isinstance(shp_pt, shp.Point)


# ---------------------------------------------------------------------------
# LineString
# ---------------------------------------------------------------------------

def test_v3_linestring_roundtrip(v3):
    ls = shp.LineString([[0, 0], [1, 0], [1, 1]])
    iso_ls = v3.to_iso_line_string(ls, iso3.LineStringType.Drainage)
    assert isinstance(iso_ls, iso3.LineString)
    assert iso_ls.points[1].north == 0
    assert iso_ls.points[1].east == 1
    assert v3.to_shapely_line_string(iso_ls).equals(ls)


def test_v3_linestring_implicit_closing(v3):
    iso_ls = iso3.LineString(
        type=iso3.LineStringType.PolygonExterior,
        points=[
            iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(0)),
            iso3.Point(type=iso3.PointType.Other, north=Decimal(0), east=Decimal(1)),
            iso3.Point(type=iso3.PointType.Other, north=Decimal(1), east=Decimal(1)),
        ],
    )
    assert shp.is_closed(v3.to_shapely_line_string(iso_ls))


def test_v4_linestring_single_point(v4):
    iso_ls = iso4.LineString(points=[
        iso4.Point(type=iso4.PointType.GuidanceReferenceA, north=Decimal(0), east=Decimal(0)),
    ])
    shp_ls = v4.to_shapely_line_string(iso_ls)
    assert len(shp_ls.coords) == 2
    assert not shp.is_valid(shp_ls)


# ---------------------------------------------------------------------------
# Polygon
# ---------------------------------------------------------------------------

def test_v3_polygon_roundtrip(v3):
    poly = shp.Polygon(
        shell=[[10, 0], [0, 0], [0, 10], [10, 0]],
        holes=[
            [[1, 1], [2, 1], [2, 2], [1, 1]],
            [[4, 4], [3, 4], [3, 3], [4, 4]],
        ],
    )
    iso_poly = v3.to_iso_polygon(poly)
    assert isinstance(iso_poly, iso3.Polygon)
    assert v3.to_shapely_polygon(iso_poly).equals(poly)


def test_v4_polygon_roundtrip(v4):
    poly = shp.Polygon(
        shell=[[10, 0], [0, 0], [0, 10], [10, 0]],
        holes=[
            [[1, 1], [2, 1], [2, 2], [1, 1]],
            [[4, 4], [3, 4], [3, 3], [4, 4]],
        ],
    )
    iso_poly = v4.to_iso_polygon(poly)
    assert isinstance(iso_poly, iso4.Polygon)
    assert v4.to_shapely_polygon(iso_poly).equals(poly)


def test_v4_polygon_implicit_shell(v4):
    iso_poly = iso4.Polygon(
        type=iso4.PolygonType.Flag,
        line_strings=[
            iso4.LineString(
                type=iso4.LineStringType.Flag,
                points=[
                    iso4.Point(type=iso4.PointType.Flag, north=Decimal(0), east=Decimal(0)),
                    iso4.Point(type=iso4.PointType.Flag, north=Decimal(0), east=Decimal(1)),
                    iso4.Point(type=iso4.PointType.Flag, north=Decimal(1), east=Decimal(1)),
                    iso4.Point(type=iso4.PointType.Flag, north=Decimal(0), east=Decimal(0)),
                ],
            )
        ],
    )
    v4.to_shapely_polygon(iso_poly)


def test__to_shapely_polygon__when_shell_missing__expect_error(v3):
    iso_poly = iso3.Polygon(
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
        v3.to_shapely_polygon(iso_poly)


def test__to_shapely_polygon__when_multiple_exterior_rings__expect_not_implemented(v3):
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
    with pytest.raises(NotImplementedError):
        v3.to_shapely_polygon(iso3.Polygon(type=iso3.PolygonType.Other, line_strings=[shell_a, shell_b]))


# ---------------------------------------------------------------------------
# Multi-geometry
# ---------------------------------------------------------------------------

def test_v3_multipoint_roundtrip(v3):
    mp = shp.MultiPoint([[0.0, 0.0], [1.0, 2.0]])
    iso_pts = v3.to_iso_point_list(mp)
    assert isinstance(iso_pts[0], iso3.Point)
    assert v3.to_shapely_multi_point(iso_pts).equals(mp)


def test_v3_multilinestring_roundtrip(v3):
    mls = shp.MultiLineString([[[0, 0], [1, 2]], [[4, 4], [5, 6]]])
    iso_lss = v3.to_iso_line_string_list(mls, iso3.LineStringType.SamplingRoute)
    assert isinstance(iso_lss[0], iso3.LineString)
    assert v3.to_shapely_multi_line_string(iso_lss).equals(mls)


def test_v3_multipolygon_roundtrip(v3):
    mp = shp.MultiPolygon([
        (((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)),
         [((0.1, 0.1), (0.1, 0.2), (0.2, 0.2), (0.2, 0.1))])
    ])
    iso_polys = v3.to_iso_polygon_list(mp)
    assert isinstance(iso_polys[0], iso3.Polygon)
    assert v3.to_shapely_multi_polygon(iso_polys).equals(mp)


# ---------------------------------------------------------------------------
# to_shapely_geom dispatch
# ---------------------------------------------------------------------------

def test__to_shapely_geom__when_v4_type_on_v3_converter__expect_not_implemented(v3):
    iso_pt = iso4.Point(type=iso4.PointType.Flag, north=Decimal(1), east=Decimal(2))
    with pytest.raises(NotImplementedError):
        v3.to_shapely_geom(iso_pt)


@pytest.mark.parametrize('wkt', [
    'POINT Z (30.5 10.2 150.0)',
    'LINESTRING Z (30.5 10.2 150.0, 40.1 20.3 200.0, 50.2 30.4 250.0)',
    'POLYGON Z ((30.5 10.2 150.0, 40.1 20.3 200.0, 50.2 30.4 250.0, 30.5 10.2 150.0))',
])
def test_3d_geoms_roundtrip(v3, wkt):
    geom = shp.from_wkt(wkt)
    iso_geom = None
    match geom:
        case shp.Point() as pt:
            iso_geom = v3.to_iso_point(pt)
        case shp.LineString() as ls:
            iso_geom = v3.to_iso_line_string(ls, iso3.LineStringType.Flag)
        case shp.Polygon() as poly:
            iso_geom = v3.to_iso_polygon(poly)
    assert iso_geom is not None
    assert v3.to_shapely_geom(iso_geom).equals(geom)
