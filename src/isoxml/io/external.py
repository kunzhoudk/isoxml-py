"""Utilities for merging ExternalFileContents objects into a TaskData tree."""

from copy import deepcopy
from dataclasses import fields

from isoxml.models.base import v3 as iso3, v4 as iso4


def merge_ext_content(
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    ext_content_map: dict[str, iso3.ExternalFileContents | iso4.ExternalFileContents],
    inplace: bool = False,
) -> tuple[iso3.Iso11783TaskData | iso4.Iso11783TaskData, dict[str, object]]:
    """Merge parsed external-file objects back into the main *task_data* tree.

    For each ``ExternalFileReference`` recorded in *task_data*, the matching
    entry from *ext_content_map* is consumed and its child elements are appended
    to the corresponding list fields on *task_data*.

    Args:
        task_data: Root TaskData to merge into.
        ext_content_map: Mapping of filename → ``ExternalFileContents``.
            Entries that are merged are removed from the mapping.
        inplace: When ``False`` (default), deep-copies both objects before
            modifying them; the originals are left unchanged.

    Returns:
        ``(merged_task_data, remaining_refs)`` where *remaining_refs* contains
        any entries from *ext_content_map* that were not referenced by the task
        data (typically binary blobs).
    """
    _task_data = task_data if inplace else deepcopy(task_data)
    _ext_map = ext_content_map if inplace else ext_content_map.copy()

    # Build a lookup: XML element name → dataclass field name on task_data.
    element_to_field: dict[str, str] = {}
    for field_meta in fields(_task_data):
        if "name" in field_meta.metadata:
            element_to_field[field_meta.metadata["name"]] = field_meta.name

    for ext_ref in _task_data.external_file_references:
        ref_obj = _ext_map.pop(ext_ref.filename)
        for value in ref_obj.__dict__.values():
            if isinstance(value, list) and value:
                field_name = element_to_field.get(value[0].Meta.name)
                if field_name and hasattr(_task_data, field_name):
                    getattr(_task_data, field_name).extend(value)

    _task_data.external_file_references = []
    return _task_data, _ext_map
