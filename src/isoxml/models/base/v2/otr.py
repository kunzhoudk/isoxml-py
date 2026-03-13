from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Otr:
    """
    OperationTechniqueReference.

    :ivar a: OperationTechniqueIdRef
    """

    class Meta:
        name = "OTR"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(OTQ|OTQ-)([0-9])+",
        }
    )
