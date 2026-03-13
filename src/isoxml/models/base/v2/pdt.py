from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Pdt:
    """
    Product.

    :ivar a: ProductId
    :ivar b: ProductDesignator
    :ivar c: ProductGroupIdRef
    :ivar d: ValuePresentationIdRef
    :ivar e: AmountDDI
    """

    class Meta:
        name = "PDT"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PDT|PDT-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
    c: None | str = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PGP|PGP-)([0-9])+",
        },
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(VPN|VPN-)([0-9])+",
        },
    )
    e: None | bytes = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "length": 2,
            "format": "base16",
        },
    )
