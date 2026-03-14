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

Version conversion::

    from isoxml import task_data_v3_to_v4

Grid encoding / decoding (requires numpy ≥ 1.26)::

    from isoxml import encode, encode_type1, encode_type2, decode
    # or: from isoxml.grid import encode, decode

ISOBUS Data Dictionary::

    from isoxml import DDEntity
    # or: from isoxml.models import DDEntity

Shapefile → grid pipeline (requires geopandas; install with ``pip install isoxml[pipeline]``)::

    from isoxml.pipeline import ShpToGridOptions, convert
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

# Version conversion
from isoxml.convert import task_data_v3_to_v4

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
    # Grid codec
    "encode",
    "encode_type1",
    "encode_type2",
    "decode",
    # Version conversion
    "task_data_v3_to_v4",
    # Models
    "DDEntity",
]
