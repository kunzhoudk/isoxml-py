"""Field-name and value mappings between ISOXML v3 and v4 models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import isoxml.models.base.v4 as iso4

ValueTransform = Callable[[Any], Any]


@dataclass(frozen=True)
class FieldMapping:
    """Mapping between a v3 field and its v4 counterpart."""

    source_field: str
    target_field: str
    forward: ValueTransform | None = None
    backward: ValueTransform | None = None

    def source_field_for_target(self, target_iso) -> str:
        """Return the source-side field name for the requested target version."""
        return self.source_field if target_iso is iso4 else self.target_field

    def target_field_for_version(self, target_iso) -> str:
        """Return the field name expected on the target-side dataclass."""
        return self.target_field if target_iso is iso4 else self.source_field

    def transform_for_target(self, value: Any, target_iso) -> Any:
        """Apply the directional value transform if one is configured."""
        transform = self.forward if target_iso is iso4 else self.backward
        if transform is None:
            return value
        return transform(value)


_MAPPINGS: dict[str, list[FieldMapping]] = {
    "Customer": [
        FieldMapping("designator", "last_name"),
    ],
    "Worker": [
        FieldMapping("designator", "last_name"),
    ],
    "Device": [
        FieldMapping("working_set_master_name", "client_name"),
    ],
    "DeviceAllocation": [
        FieldMapping("working_set_master_name_value", "client_name_value"),
        FieldMapping("working_set_master_name_mask", "client_name_mask"),
    ],
    "ProductAllocation": [
        FieldMapping("amount_ddi", "quantity_ddi"),
        FieldMapping("amount_value", "quantity_value"),
    ],
    "Point": [
        FieldMapping(
            "colour",
            "colour",
            forward=lambda value: str(value) if isinstance(value, int) else value,
            backward=lambda value: (
                int(value) if isinstance(value, str) and value.isdigit() else value
            ),
        ),
    ],
    "AllocationStamp": [
        FieldMapping(
            "position",
            "positions",
            forward=lambda value: [value] if value is not None else [],
            backward=lambda value: value[0] if value else None,
        ),
    ],
}


def get_field_mapping(
    cls_name: str, target_field_name: str, target_iso
) -> FieldMapping | None:
    """Return the mapping describing how to populate a target dataclass field."""
    for mapping in _MAPPINGS.get(cls_name, []):
        if mapping.target_field_for_version(target_iso) == target_field_name:
            return mapping
    return None
