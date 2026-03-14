"""Functions for writing ISOXML TaskData to directories, ZIP archives, and XML text."""

from pathlib import Path
from zipfile import ZipFile

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

_serializer = XmlSerializer(
    config=SerializerConfig(
        xml_version='1.0',
        encoding='UTF-8',
        indent='    ',
    )
)


def to_xml(task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData) -> str:
    """Serialize a TaskData object to an XML string."""
    return _serializer.render(task_data)


def write_to_dir(
        dir_path: Path,
        task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
        ext_refs: dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents] | None = None,
) -> None:
    """Write ``TASKDATA.XML`` and optional external references into *dir_path*.

    Values in *ext_refs* may be:
    - ``bytes`` → written as ``<key>.bin``
    - ``ExternalFileContents`` → written as ``<key>.XML``
    """
    ext_refs = ext_refs or {}
    xml_path = dir_path / 'TASKDATA.XML'
    with open(xml_path, 'w', encoding='utf-8') as fh:
        _serializer.write(fh, task_data)

    for ref_name, ref_data in ext_refs.items():
        if isinstance(ref_data, bytes):
            with open(dir_path / (ref_name + '.bin'), 'wb') as fh:
                fh.write(ref_data)
        elif isinstance(ref_data, (iso3.ExternalFileContents, iso4.ExternalFileContents)):
            with open(dir_path / (ref_name + '.XML'), 'w', encoding='utf-8') as fh:
                _serializer.write(fh, ref_data)
        else:
            raise ValueError(f"Unsupported type {type(ref_data)!r} for reference '{ref_name}'.")


def write_to_zip(
        target,
        task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
        ext_refs: dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents] | None = None,
        include_folder: bool = True,
) -> None:
    """Write task data and references into a ZIP archive.

    Args:
        target: A file path or file-like object accepted by ``ZipFile``.
        include_folder: When ``True``, place all files under a ``TASKDATA/``
            folder inside the archive.
    """
    ext_refs = ext_refs or {}
    prefix = 'TASKDATA/' if include_folder else ''

    with ZipFile(target, 'w') as zf:
        xml_bytes = to_xml(task_data).encode('utf-8')
        with zf.open(prefix + 'TASKDATA.XML', 'w') as fh:
            fh.write(xml_bytes)

        for ref_name, ref_data in ext_refs.items():
            if isinstance(ref_data, bytes):
                with zf.open(prefix + ref_name + '.bin', 'w') as fh:
                    fh.write(ref_data)
            elif isinstance(ref_data, (iso3.ExternalFileContents, iso4.ExternalFileContents)):
                xml_bytes = _serializer.render(ref_data).encode('utf-8')
                with zf.open(prefix + ref_name + '.XML', 'w') as fh:
                    fh.write(xml_bytes)
            else:
                raise ValueError(f"Unsupported type {type(ref_data)!r} for reference '{ref_name}'.")
