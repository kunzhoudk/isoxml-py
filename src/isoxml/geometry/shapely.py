"""Shapely <-> ISOXML geometry converters."""

from decimal import Decimal
from types import ModuleType

import shapely as shp

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4


class _ShapelyConverter:
    def __init__(self, iso_module: ModuleType) -> None:
        self.iso = iso_module

    def _iso_point_from_coords(
        self,
        lon: float,
        lat: float,
        alt: float | None = None,
        pnt_type=None,
        **kwargs,
    ):
        if pnt_type is None:
            pnt_type = self.iso.PointType.Other
        return self.iso.Point(
            type=pnt_type,
            north=round(Decimal(lat), 9),
            east=round(Decimal(lon), 9),
            up=int(alt * 1e3) if alt else None,
            **kwargs,
        )

    @staticmethod
    def _coords_from_iso_point(iso_pnt) -> tuple[float, float] | tuple[float, float, float]:
        if iso_pnt.up:
            return float(iso_pnt.east), float(iso_pnt.north), float(iso_pnt.up * 1e-3)
        return float(iso_pnt.east), float(iso_pnt.north)

    def to_iso_point(self, point: shp.Point, pnt_type=None, **kwargs):
        if pnt_type is None:
            pnt_type = self.iso.PointType.Other
        return self._iso_point_from_coords(
            lon=point.x,
            lat=point.y,
            alt=point.z if point.has_z else None,
            pnt_type=pnt_type,
            **kwargs,
        )

    def to_shapely_point(self, iso_pnt) -> shp.Point:
        return shp.Point(self._coords_from_iso_point(iso_pnt))

    def to_iso_line_string(self, line: shp.LineString, line_type, **kwargs):
        return self.iso.LineString(
            type=line_type,
            points=[self._iso_point_from_coords(*coord) for coord in line.coords],
            **kwargs,
        )

    def to_shapely_line_string(self, iso_line) -> shp.LineString:
        coords = [self._coords_from_iso_point(iso_pnt) for iso_pnt in iso_line.points]
        if iso_line.type in (
            iso3.LineStringType.PolygonExterior,
            iso3.LineStringType.PolygonInterior,
        ):
            if coords[0] != coords[-1]:
                coords.append(coords[0])
        if len(coords) == 1:
            coords.append(coords[0])
        return shp.LineString(coords)

    def to_iso_polygon(self, shp_polygon: shp.Polygon, poly_type=None, **kwargs):
        if poly_type is None:
            poly_type = self.iso.PolygonType.Other
        shell = self.to_iso_line_string(
            shp_polygon.exterior,
            self.iso.LineStringType.PolygonExterior,
        )
        inner = [
            self.to_iso_line_string(
                shp_line_string,
                self.iso.LineStringType.PolygonInterior,
            )
            for shp_line_string in shp_polygon.interiors
        ]
        return self.iso.Polygon(type=poly_type, line_strings=[shell] + inner, **kwargs)

    def to_shapely_polygon(self, iso_polygon) -> shp.Polygon:
        holes = []
        shell = None
        for iso_line_string in iso_polygon.line_strings:
            shp_line = self.to_shapely_line_string(iso_line_string)
            match iso_line_string.type:
                case (
                    iso3.LineStringType.PolygonInterior
                    | iso4.LineStringType.PolygonInterior
                ):
                    holes.append(shp_line)
                case _:
                    if shell is not None:
                        raise NotImplementedError(
                            """
                            The conversion of MultiPolygons in the style of v3 is not supported (yet).
                            You can support the development of this library by sending us a
                            sample ISOXML file that caused this error.
                            """
                        )
                    shell = shp_line
        if shell is None:
            raise ValueError("provides isoxml polygon did not contain a PolygonExterior")
        return shp.Polygon(shell=shell, holes=holes)

    def to_iso_point_list(self, multi_point: shp.MultiPoint, pnt_type=None, **kwargs) -> list:
        if pnt_type is None:
            pnt_type = self.iso.PointType.Other
        return [self.to_iso_point(shp_point, pnt_type, **kwargs) for shp_point in multi_point.geoms]

    def to_shapely_multi_point(self, iso_points: list) -> shp.MultiPoint:
        return shp.MultiPoint([self.to_shapely_point(iso_point) for iso_point in iso_points])

    def to_iso_line_string_list(self, multi_line: shp.MultiLineString, lsg_type, **kwargs) -> list:
        return [self.to_iso_line_string(shp_line, lsg_type, **kwargs) for shp_line in multi_line.geoms]

    def to_shapely_multi_line_string(self, iso_lines: list) -> shp.MultiLineString:
        return shp.MultiLineString([self.to_shapely_line_string(iso_line) for iso_line in iso_lines])

    def to_iso_polygon_list(self, multi_polygon: shp.MultiPolygon, pln_type=None, **kwargs) -> list:
        if pln_type is None:
            pln_type = self.iso.PolygonType.Other
        return [self.to_iso_polygon(shp_polygon, pln_type, **kwargs) for shp_polygon in multi_polygon.geoms]

    def to_shapely_multi_polygon(self, iso_polygons: list) -> shp.MultiPolygon:
        return shp.MultiPolygon([self.to_shapely_polygon(iso_polygon) for iso_polygon in iso_polygons])

    def to_shapely_geom(self, iso_geometry) -> shp.Geometry:
        match type(iso_geometry):
            case self.iso.Point:
                return self.to_shapely_point(iso_geometry)
            case self.iso.LineString:
                return self.to_shapely_line_string(iso_geometry)
            case self.iso.Polygon:
                return self.to_shapely_polygon(iso_geometry)
            case _:
                raise NotImplementedError(f"Unknown iso geometry {type(iso_geometry)}")


class ShapelyConverterV3(_ShapelyConverter):
    def __init__(self):
        super().__init__(iso3)


class ShapelyConverterV4(_ShapelyConverter):
    def __init__(self):
        super().__init__(iso4)


__all__ = ["ShapelyConverterV3", "ShapelyConverterV4"]
