from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Otq:
    """
    OperationTechnique.

    :ivar a: OperationTechniqueId
    :ivar b: OperationTechniqueDesignator
    """

    class Meta:
        name = "OTQ"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(OTQ|OTQ-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
