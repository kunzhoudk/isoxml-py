from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.asp import Asp


@dataclass(kw_only=True)
class Wan:
    """
    WorkerAllocation.

    :ivar asp: AllocationStamp
    :ivar a: WorkerIdRef
    """

    class Meta:
        name = "WAN"

    asp: None | Asp = field(
        default=None,
        metadata={
            "name": "ASP",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(WKR|WKR-)([0-9])+",
        }
    )
