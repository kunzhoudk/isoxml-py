from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Cvt:
    """
    CropVariety.

    :ivar a: CropVarietyId
    :ivar b: CropVarietyDesignator
    """

    class Meta:
        name = "CVT"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CVT|CVT-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
