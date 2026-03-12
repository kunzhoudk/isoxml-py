from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Pdv:
    """
    ProcessDataVariable.

    :ivar pdv: ProcessDataVariable
    :ivar a: ProcessDataDDI
    :ivar b: ProcessDataValue
    :ivar c: ProductIdRef
    :ivar d: DeviceElementIdRef
    :ivar e: ValuePresentationIdRef
    """

    class Meta:
        name = "PDV"

    pdv: list[Pdv] = field(
        default_factory=list,
        metadata={
            "name": "PDV",
            "type": "Element",
        },
    )
    a: bytes = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "length": 2,
            "format": "base16",
        }
    )
    b: int = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": -2147483648,
            "max_inclusive": 2147483647,
        }
    )
    c: None | str = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PDT|PDT-)([0-9])+",
        },
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        },
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(VPN|VPN-)([0-9])+",
        },
    )
