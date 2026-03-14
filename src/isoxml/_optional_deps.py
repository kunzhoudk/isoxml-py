"""Helpers for lazily importing optional third-party dependencies."""

from __future__ import annotations


def require_geopandas():
    try:
        import geopandas as gpd
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "geopandas is required for shapefile conversion. "
            "Install optional dependencies with `pip install .[dev]`."
        ) from exc
    return gpd


def require_xmlschema():
    try:
        import xmlschema
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "xmlschema is required for XSD validation. "
            "Install optional dependencies with `pip install .[dev]`."
        ) from exc
    return xmlschema
