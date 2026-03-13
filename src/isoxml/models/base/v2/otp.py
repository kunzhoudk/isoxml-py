from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Otp:
    """
    OperTechPractice.

    :ivar a: CulturalPracticeIdRef
    :ivar b: OperationTechniqueIdRef
    """

    class Meta:
        name = "OTP"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CPC|CPC-)([0-9])+",
        }
    )
    b: None | str = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(OTQ|OTQ-)([0-9])+",
        },
    )
