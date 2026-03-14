"""Convert an ISOXML v4 dataclass tree to v3."""

import dataclasses
from enum import Enum

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

# Index v3 classes and enums by name once at import time.
_V3_CLASSES: dict[str, type] = {
    name: obj
    for name, obj in vars(iso3).items()
    if isinstance(obj, type) and dataclasses.is_dataclass(obj)
}

_V3_ENUMS: dict[str, type[Enum]] = {
    name: obj
    for name, obj in vars(iso3).items()
    if isinstance(obj, type) and issubclass(obj, Enum) and obj is not Enum
}


def _convert_enum(v4_val: Enum) -> Enum | None:
    """Return the v3 enum member whose value matches *v4_val*.

    Returns ``None`` when the numeric value no longer exists in v3 (e.g.
    ``TaskStatus.Template`` and ``TaskStatus.Canceled`` are v4-only).
    """
    v3_enum = _V3_ENUMS.get(type(v4_val).__name__)
    if v3_enum is None:
        return None  # enum class does not exist in v3
    try:
        return v3_enum(v4_val.value)
    except ValueError:
        return None  # value exists only in v4


def _convert_value(v4_val):
    """Recursively convert a single field value."""
    if v4_val is None:
        return None
    if isinstance(v4_val, list):
        return [c for item in v4_val if (c := _convert_value(item)) is not None]
    if isinstance(v4_val, Enum):
        return _convert_enum(v4_val)
    if dataclasses.is_dataclass(v4_val) and not isinstance(v4_val, type):
        return _convert_dataclass(v4_val)
    return v4_val


def _convert_dataclass(v4_obj):
    """Convert a single v4 dataclass instance to the equivalent v3 class.

    Returns ``None`` when the v4 class has no v3 counterpart (e.g.
    ``GuidanceGroup``, ``ControlAssignment``), so callers can skip it.
    """
    cls_name = type(v4_obj).__name__
    v3_cls = _V3_CLASSES.get(cls_name)
    if v3_cls is None:
        return None  # v4-only type – silently drop

    v4_field_names = {f.name for f in dataclasses.fields(v4_obj)}
    v3_fields = {f.name: f for f in dataclasses.fields(v3_cls)}

    kwargs: dict = {}
    for fname, v3_f in v3_fields.items():
        if not v3_f.init:
            continue  # e.g. version_major is set automatically
        if fname not in v4_field_names:
            continue  # v3-only field – use its default

        v4_val = getattr(v4_obj, fname)
        converted = _convert_value(v4_val)

        # Point.colour changed from str (v4) to int (v3).
        if cls_name == "Point" and fname == "colour" and isinstance(converted, str):
            try:
                converted = int(converted)
            except (ValueError, TypeError):
                converted = None

        kwargs[fname] = converted

    return v3_cls(**kwargs)


def task_data_v4_to_v3(v4_data: iso4.Iso11783TaskData) -> iso3.Iso11783TaskData:
    """Convert a v4 ``Iso11783TaskData`` tree to v3.

    Fields that only exist in v4 (``guidance_groups``, ``control_assignments``,
    ``attached_files``, …) are silently dropped.  Enum values with no v3
    equivalent (``TaskStatus.Template``, ``TaskStatus.Canceled``) are mapped to
    ``None``.

    Args:
        v4_data: A parsed v4 task-data object.

    Returns:
        An equivalent v3 ``Iso11783TaskData`` instance.

    Raises:
        TypeError: If *v4_data* is not an ``iso4.Iso11783TaskData`` instance.
    """
    if not isinstance(v4_data, iso4.Iso11783TaskData):
        raise TypeError(
            f"Expected iso4.Iso11783TaskData, got {type(v4_data).__name__}"
        )
    return _convert_dataclass(v4_data)
