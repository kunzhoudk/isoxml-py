"""Compatibility wrapper for the legacy `isoxml.converter.shapely_geom` module."""

from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4

__all__ = ["ShapelyConverterV3", "ShapelyConverterV4"]
