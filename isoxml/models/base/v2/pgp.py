from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Pgp:
    """
    ProductGroup.

    :ivar a: ProductGroupId
    :ivar b: ProductGroupDesignator
    """

    class Meta:
        name = "PGP"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PGP|PGP-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
