"""Public package surface for isoxml."""

from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grids import (
    from_numpy_array,
    from_numpy_array_to_type_1,
    from_numpy_array_to_type_2,
    to_numpy_array,
)
from isoxml.io import (
    dump_taskdata_to_text,
    load_taskdata_from_path,
    load_taskdata_from_text,
    load_taskdata_from_zip,
    merge_external_file_contents,
    write_taskdata_dir,
    write_taskdata_zip,
)
from isoxml.prescriptions import (
    GridFromShpOptions,
    GridFromShpResult,
    build_grid_taskdata_from_shapefile,
    convert_grid_from_shp,
)
from isoxml.validation import validate_taskdata_xsd

__all__ = [
    "GridFromShpOptions",
    "GridFromShpResult",
    "ShapelyConverterV3",
    "ShapelyConverterV4",
    "build_grid_taskdata_from_shapefile",
    "convert_grid_from_shp",
    "dump_taskdata_to_text",
    "from_numpy_array",
    "from_numpy_array_to_type_1",
    "from_numpy_array_to_type_2",
    "load_taskdata_from_path",
    "load_taskdata_from_text",
    "load_taskdata_from_zip",
    "merge_external_file_contents",
    "to_numpy_array",
    "validate_taskdata_xsd",
    "write_taskdata_dir",
    "write_taskdata_zip",
]
