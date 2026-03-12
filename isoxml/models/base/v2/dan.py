from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.asp import Asp


@dataclass(kw_only=True)
class Dan:
    """
    DeviceAllocation.

    :ivar asp: AllocationStamp
    :ivar a: WorkingSetMasterNameValue
    :ivar b: WorkingSetMasterNameMask
    :ivar c: DeviceIdRef
    """

    class Meta:
        name = "DAN"

    asp: None | Asp = field(
        default=None,
        metadata={
            "name": "ASP",
            "type": "Element",
        },
    )
    a: bytes = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "length": 8,
            "format": "base16",
        }
    )
    b: None | bytes = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "length": 8,
            "format": "base16",
        },
    )
    c: None | str = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DVC|DVC-)([0-9])+",
        },
    )
