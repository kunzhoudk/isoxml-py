"""Bidirectional conversion between Shapely geometries and ISOXML geometry objects."""

from decimal import Decimal
from types import ModuleType

import shapely as shp

import isoxml.models.base.v3 as _iso3
import isoxml.models.base.v4 as _iso4


class _ShapelyConverter:
    """Base converter shared by both ISOXML v3 and v4 geometry models."""

    def __init__(self, iso_module: ModuleType) -> None:
        self._iso = iso_module

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_iso_point(
        self,
        lon: float,
        lat: float,
        alt: float | None = None,
        pnt_type=None,
        **kwargs,
    ):
        if pnt_type is None:
            pnt_type = self._iso.PointType.Other
        return self._iso.Point(
            type=pnt_type,
            north=round(Decimal(lat), 9),
            east=round(Decimal(lon), 9),
            up=int(alt * 1e3) if alt is not None else None,
            **kwargs,
        )

    @staticmethod
    def _coords_from_iso_point(iso_pnt) -> tuple:
        if iso_pnt.up:
            return float(iso_pnt.east), float(iso_pnt.north), float(iso_pnt.up * 1e-3)
        return float(iso_pnt.east), float(iso_pnt.north)

    # ------------------------------------------------------------------
    # Point
    # ------------------------------------------------------------------

    def to_iso_point(self, point: shp.Point, pnt_type=None, **kwargs):
        """Convert a Shapely ``Point`` to an ISOXML ``Point``."""
        return self._make_iso_point(
            lon=point.x,
            lat=point.y,
            alt=point.z if point.has_z else None,
            pnt_type=pnt_type,
            **kwargs,
        )

    def to_shapely_point(self, iso_pnt) -> shp.Point:
        """Convert an ISOXML ``Point`` to a Shapely ``Point``."""
        return shp.Point(self._coords_from_iso_point(iso_pnt))

    # ------------------------------------------------------------------
    # LineString
    # ------------------------------------------------------------------

    def to_iso_line_string(self, line: shp.LineString, line_type, **kwargs):
        """Convert a Shapely ``LineString`` to an ISOXML ``LineString``."""
        return self._iso.LineString(
            type=line_type,
            points=[self._make_iso_point(*coord) for coord in line.coords],
            **kwargs,
        )

    def to_shapely_line_string(self, iso_line) -> shp.LineString:
        """Convert an ISOXML ``LineString`` to a Shapely ``LineString``."""
        coords = [self._coords_from_iso_point(p) for p in iso_line.points]

        # v3 exterior/interior rings are implicitly closed; v4 rings are explicit.
        # Using self._iso ensures the check is version-aware.
        if iso_line.type in (
            self._iso.LineStringType.PolygonExterior,
            self._iso.LineStringType.PolygonInterior,
        ):
            if coords[0] != coords[-1]:
                coords.append(coords[0])

        # A single-point LineString is degenerate but valid in some v4 guidance exports.
        if len(coords) == 1:
            coords.append(coords[0])

        return shp.LineString(coords)

    # ------------------------------------------------------------------
    # Polygon
    # ------------------------------------------------------------------

    def to_iso_polygon(self, shp_polygon: shp.Polygon, poly_type=None, **kwargs):
        """Convert a Shapely ``Polygon`` (with optional holes) to an ISOXML ``Polygon``."""
        if poly_type is None:
            poly_type = self._iso.PolygonType.Other
        exterior = self.to_iso_line_string(
            shp_polygon.exterior, self._iso.LineStringType.PolygonExterior
        )
        interiors = [
            self.to_iso_line_string(ring, self._iso.LineStringType.PolygonInterior)
            for ring in shp_polygon.interiors
        ]
        return self._iso.Polygon(
            type=poly_type,
            line_strings=[exterior] + interiors,
            **kwargs,
        )

    def to_shapely_polygon(self, iso_polygon) -> shp.Polygon:
        """Convert an ISOXML ``Polygon`` to a Shapely ``Polygon``."""
        shell = None
        holes = []
        for iso_ls in iso_polygon.line_strings:
            shp_ls = self.to_shapely_line_string(iso_ls)
            if iso_ls.type == self._iso.LineStringType.PolygonInterior:
                holes.append(shp_ls)
            else:
                if shell is not None:
                    raise NotImplementedError(
                        "Conversion of multi-exterior-ring Polygons (v3 style) is not "
                        "supported. Please open an issue with a sample ISOXML file."
                    )
                shell = shp_ls
        if shell is None:
            raise ValueError("ISOXML Polygon contains no PolygonExterior LineString.")
        return shp.Polygon(shell=shell, holes=holes)

    # ------------------------------------------------------------------
    # Multi-geometry helpers
    # ------------------------------------------------------------------

    def to_iso_point_list(
        self, multi_point: shp.MultiPoint, pnt_type=None, **kwargs
    ) -> list:
        """Convert a Shapely ``MultiPoint`` to a list of ISOXML ``Point`` objects."""
        if pnt_type is None:
            pnt_type = self._iso.PointType.Other
        return [self.to_iso_point(p, pnt_type, **kwargs) for p in multi_point.geoms]

    def to_shapely_multi_point(self, iso_points: list) -> shp.MultiPoint:
        """Convert a list of ISOXML ``Point`` objects to a Shapely ``MultiPoint``."""
        return shp.MultiPoint([self.to_shapely_point(p) for p in iso_points])

    def to_iso_line_string_list(
        self, multi_line: shp.MultiLineString, lsg_type, **kwargs
    ) -> list:
        """Convert a Shapely ``MultiLineString`` to a list of ISOXML ``LineString`` objects."""
        return [
            self.to_iso_line_string(ls, lsg_type, **kwargs) for ls in multi_line.geoms
        ]

    def to_shapely_multi_line_string(self, iso_lines: list) -> shp.MultiLineString:
        """Convert a list of ISOXML ``LineString`` objects to a Shapely ``MultiLineString``."""
        return shp.MultiLineString(
            [self.to_shapely_line_string(ls) for ls in iso_lines]
        )

    def to_iso_polygon_list(
        self, multi_polygon: shp.MultiPolygon, pln_type=None, **kwargs
    ) -> list:
        """Convert a Shapely ``MultiPolygon`` to a list of ISOXML ``Polygon`` objects."""
        if pln_type is None:
            pln_type = self._iso.PolygonType.Other
        return [self.to_iso_polygon(p, pln_type, **kwargs) for p in multi_polygon.geoms]

    def to_shapely_multi_polygon(self, iso_polygons: list) -> shp.MultiPolygon:
        """Convert a list of ISOXML ``Polygon`` objects to a Shapely ``MultiPolygon``."""
        return shp.MultiPolygon([self.to_shapely_polygon(p) for p in iso_polygons])

    def to_shapely_geom(self, iso_geometry) -> shp.Geometry:
        """Dispatch an ISOXML geometry to the matching ``to_shapely_*`` method."""
        match type(iso_geometry):
            case self._iso.Point:
                return self.to_shapely_point(iso_geometry)
            case self._iso.LineString:
                return self.to_shapely_line_string(iso_geometry)
            case self._iso.Polygon:
                return self.to_shapely_polygon(iso_geometry)
            case _:
                raise NotImplementedError(
                    f"No Shapely converter for ISOXML type {type(iso_geometry).__name__!r}."
                )


class ShapelyConverterV3(_ShapelyConverter):
    """Converter for ISOXML **v3** geometry models."""

    def __init__(self) -> None:
        super().__init__(_iso3)


class ShapelyConverterV4(_ShapelyConverter):
    """Converter for ISOXML **v4** geometry models."""

    def __init__(self) -> None:
        super().__init__(_iso4)
