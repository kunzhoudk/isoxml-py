from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.asp import Asp
from isoxml.models.base.v2.pan_d import PanD


@dataclass(kw_only=True)
class Pan:
    """
    ProductAllocation.

    :ivar asp:
    :ivar a: ProductIdRef
    :ivar b: AmountDDI
    :ivar c: AmountValue
    :ivar d: TransferMode
    :ivar e: DeviceElementIdRef
    :ivar f: ValuePresentationIdRef
    """

    class Meta:
        name = "PAN"

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
            "pattern": r"(PDT|PDT-)([0-9])+",
        }
    )
    b: None | bytes = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "length": 2,
            "format": "base16",
        },
    )
    c: None | int = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 2147483647,
        },
    )
    d: None | PanD = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
        },
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        },
    )
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(VPN|VPN-)([0-9])+",
        },
    )
