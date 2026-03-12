from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.otr import Otr


@dataclass(kw_only=True)
class Cpc:
    """
    CulturalPractice.

    :ivar otr: OperationTechniqueReference
    :ivar a: CulturalPracticeId
    :ivar b: CulturalPracticeDesignator
    """

    class Meta:
        name = "CPC"

    otr: list[Otr] = field(
        default_factory=list,
        metadata={
            "name": "OTR",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CPC|CPC-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
