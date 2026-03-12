from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.det_c import DetC
from isoxml.models.base.v2.dor import Dor


@dataclass(kw_only=True)
class Det:
    """
    DeviceElement.

    :ivar dor: DeviceObjectReference
    :ivar a: DeviceElementId
    :ivar b: DeviceElementObjectId
    :ivar c: DeviceElementType
    :ivar d: DeviceElementDesignator
    :ivar e: DeviceElementNumber
    :ivar f: ParentObjectId
    """

    class Meta:
        name = "DET"

    dor: list[Dor] = field(
        default_factory=list,
        metadata={
            "name": "DOR",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        }
    )
    b: int = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
        }
    )
    c: DetC = field(
        metadata={
            "name": "C",
            "type": "Attribute",
        }
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    e: int = field(
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4095,
        }
    )
    f: int = field(
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 65534,
        }
    )
