"""Public package surface for isoxml."""

from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grids import (
    decode_grid_binary,
    encode_grid_binary,
    encode_grid_type_1_binary,
    encode_grid_type_2_binary,
)
from isoxml.io import (
    dump_taskdata_to_text,
    load_taskdata_from_path,
    load_taskdata_from_text,
    load_taskdata_from_zip,
    merge_external_file_contents,
    write_taskdata_to_dir,
    write_taskdata_to_zip,
)
from isoxml.prescriptions import (
    GridFromShpOptions,
    GridFromShpResult,
    build_grid_taskdata_from_shapefile,
)
from isoxml.validation import validate_taskdata_xsd

__all__ = [
    "GridFromShpOptions",
    "GridFromShpResult",
    "ShapelyConverterV3",
    "ShapelyConverterV4",
    "build_grid_taskdata_from_shapefile",
    "decode_grid_binary",
    "dump_taskdata_to_text",
    "encode_grid_binary",
    "encode_grid_type_1_binary",
    "encode_grid_type_2_binary",
    "load_taskdata_from_path",
    "load_taskdata_from_text",
    "load_taskdata_from_zip",
    "merge_external_file_contents",
    "validate_taskdata_xsd",
    "write_taskdata_to_dir",
    "write_taskdata_to_zip",
]
