from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Dor:
    """
    DeviceObjectReference.

    :ivar a: DeviceObjectId
    """

    class Meta:
        name = "DOR"

    a: int = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
        }
    )
