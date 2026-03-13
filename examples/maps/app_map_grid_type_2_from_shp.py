"""Compatibility entry point for the grid-from-shapefile CLI example."""

from isoxml.cli.grid_from_shp import build_isoxml_from_shp, main, options_from_args, parse_args

__all__ = ["build_isoxml_from_shp", "main", "options_from_args", "parse_args"]


if __name__ == "__main__":
    main()
