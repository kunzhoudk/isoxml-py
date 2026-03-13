from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Cnn:
    """
    Connection.

    :ivar a: DeviceIdRef_0
    :ivar b: DeviceElementIdRef_0
    :ivar c: DeviceIdRef_1
    :ivar d: DeviceElementIdRef_1
    """

    class Meta:
        name = "CNN"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DVC|DVC-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        }
    )
    c: str = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DVC|DVC-)([0-9])+",
        }
    )
    d: str = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        }
    )
