"""isoxml – Python library for reading and writing ISOXML TaskData (ISO 11783-10).

Quick-start
-----------
Reading::

    from isoxml import read_from_path, read_from_zip, read_from_xml

Writing::

    from isoxml import to_xml, write_to_dir, write_to_zip

Geometry conversion (requires shapely ≥ 2.0)::

    from isoxml import ShapelyConverterV3, ShapelyConverterV4
    # or: from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4

Grid encoding / decoding (requires numpy ≥ 1.26)::

    from isoxml import encode, encode_type1, encode_type2, decode
    # or: from isoxml.grid import encode, decode

ISOBUS Data Dictionary::

    from isoxml import DDEntity
    # or: from isoxml.models import DDEntity

Vector → task-data pipeline::

    from isoxml.pipeline import VectorToTaskDataOptions, convert

Task-data version conversion::

    from isoxml import convert_taskdata_versions
"""

# I/O
from isoxml.io import (
    read_from_path,
    read_from_xml,
    read_from_zip,
    to_xml,
    write_to_dir,
    write_to_zip,
    merge_ext_content,
)

# Geometry converters
from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4

# High-level task-data version conversion
from isoxml.pipeline import (
    VectorToTaskDataOptions,
    VectorToTaskDataResult,
    TaskDataVersionConversionResult,
    convert_taskdata_versions,
    validate_taskdata_xsd,
)
from isoxml.xsd_validation import validate_xsd

# Grid codec
from isoxml.grid import decode, encode, encode_type1, encode_type2

# Data Dictionary
from isoxml.models import DDEntity

__all__ = [
    # I/O
    "read_from_path",
    "read_from_xml",
    "read_from_zip",
    "to_xml",
    "write_to_dir",
    "write_to_zip",
    "merge_ext_content",
    # Geometry
    "ShapelyConverterV3",
    "ShapelyConverterV4",
    "VectorToTaskDataOptions",
    "VectorToTaskDataResult",
    # Grid codec
    "encode",
    "encode_type1",
    "encode_type2",
    "decode",
    "TaskDataVersionConversionResult",
    "convert_taskdata_versions",
    "validate_taskdata_xsd",
    "validate_xsd",
    # Models
    "DDEntity",
]
