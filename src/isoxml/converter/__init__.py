"""Legacy converter namespace kept for backwards compatibility."""

from isoxml.converter.np_grid import (
    from_numpy_array,
    from_numpy_array_to_type_1,
    from_numpy_array_to_type_2,
    to_numpy_array,
)
from isoxml.converter.shapely_geom import ShapelyConverterV3, ShapelyConverterV4

__all__ = [
    "from_numpy_array",
    "from_numpy_array_to_type_1",
    "from_numpy_array_to_type_2",
    "to_numpy_array",
    "ShapelyConverterV3",
    "ShapelyConverterV4",
]
