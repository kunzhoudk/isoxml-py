from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.xfr_b import XfrB


@dataclass(kw_only=True)
class Xfr:
    """
    ExternalFileReference.

    :ivar a: Filename
    :ivar b: Filetype
    """

    class Meta:
        name = "XFR"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "length": 8,
            "pattern": r"(CCG|CCT|CLD|CPC|CTP|CTR|DVC|FRM|OTQ|PDT|PFD|PGP|TSK|VPN|WKR)[0-9][0-9][0-9][0-9][0-9]",
        }
    )
    b: XfrB = field(
        metadata={
            "name": "B",
            "type": "Attribute",
        }
    )
