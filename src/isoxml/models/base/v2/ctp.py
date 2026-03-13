from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.cvt import Cvt


@dataclass(kw_only=True)
class Ctp:
    """
    CropType.

    :ivar cvt: CropVariety
    :ivar a: CropTypeId
    :ivar b: CropTypeDesignator
    """

    class Meta:
        name = "CTP"

    cvt: list[Cvt] = field(
        default_factory=list,
        metadata={
            "name": "CVT",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CTP|CTP-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
