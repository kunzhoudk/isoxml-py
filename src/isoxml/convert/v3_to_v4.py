"""Convert an ISOXML v3 dataclass tree to v4."""

import dataclasses
from enum import Enum

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

# Index v4 classes and enums by name once at import time.
_V4_CLASSES: dict[str, type] = {
    name: obj
    for name, obj in vars(iso4).items()
    if isinstance(obj, type) and dataclasses.is_dataclass(obj)
}

_V4_ENUMS: dict[str, type[Enum]] = {
    name: obj
    for name, obj in vars(iso4).items()
    if isinstance(obj, type) and issubclass(obj, Enum) and obj is not Enum
}


def _convert_enum(v3_val: Enum) -> Enum | None:
    """Return the v4 enum member whose value matches *v3_val*.

    Returns ``None`` when the numeric value no longer exists in v4 (shouldn't
    happen for standard fields, but guards against future schema changes).
    """
    v4_enum = _V4_ENUMS.get(type(v3_val).__name__)
    if v4_enum is None:
        return v3_val  # no v4 counterpart – pass through unchanged
    try:
        return v4_enum(v3_val.value)
    except ValueError:
        return None


def _convert_value(v3_val):
    """Recursively convert a single field value."""
    if v3_val is None:
        return None
    if isinstance(v3_val, list):
        return [_convert_value(item) for item in v3_val]
    if isinstance(v3_val, Enum):
        return _convert_enum(v3_val)
    if dataclasses.is_dataclass(v3_val) and not isinstance(v3_val, type):
        return _convert_dataclass(v3_val)
    return v3_val


def _convert_dataclass(v3_obj):
    """Convert a single v3 dataclass instance to the equivalent v4 class."""
    cls_name = type(v3_obj).__name__
    v4_cls = _V4_CLASSES.get(cls_name)
    if v4_cls is None:
        raise TypeError(f"No v4 dataclass found for v3 type '{cls_name}'")

    v3_field_names = {f.name for f in dataclasses.fields(v3_obj)}
    kwargs: dict = {}

    for v4_f in dataclasses.fields(v4_cls):
        if not v4_f.init:
            continue  # e.g. version_major is set automatically
        if v4_f.name not in v3_field_names:
            continue  # v4-only field – use its default

        v3_val = getattr(v3_obj, v4_f.name)
        converted = _convert_value(v3_val)

        # Point.colour changed from int (v3) to str (v4).
        if cls_name == "Point" and v4_f.name == "colour" and isinstance(converted, int):
            converted = str(converted)

        kwargs[v4_f.name] = converted

    return v4_cls(**kwargs)


def task_data_v3_to_v4(v3_data: iso3.Iso11783TaskData) -> iso4.Iso11783TaskData:
    """Convert a v3 ``Iso11783TaskData`` tree to v4.

    All fields shared between v3 and v4 are copied verbatim (with enum values
    re-mapped by their numeric string so that, for example, ``TaskStatus.Initial``
    becomes ``TaskStatus.Planned``).  Fields that only exist in v4
    (``guidance_groups``, ``control_assignments``, …) are left at their default
    empty-list values.

    Args:
        v3_data: A parsed v3 task-data object.

    Returns:
        An equivalent v4 ``Iso11783TaskData`` instance.

    Raises:
        TypeError: If *v3_data* is not an ``iso3.Iso11783TaskData`` instance.
    """
    if not isinstance(v3_data, iso3.Iso11783TaskData):
        raise TypeError(
            f"Expected iso3.Iso11783TaskData, got {type(v3_data).__name__}"
        )
    return _convert_dataclass(v3_data)
