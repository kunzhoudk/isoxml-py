from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Frm:
    """
    Farm.

    :ivar a: FarmId
    :ivar b: FarmDesignator
    :ivar c: FarmStreet
    :ivar d: FarmPOBox
    :ivar e: FarmPostalCode
    :ivar f: FarmCity
    :ivar g: FarmState
    :ivar h: FarmCountry
    :ivar i: CustomerIdRef
    """

    class Meta:
        name = "FRM"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(FRM|FRM-)([0-9])+",
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
            "max_length": 32,
        },
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "max_length": 10,
        },
    )
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    g: None | str = field(
        default=None,
        metadata={
            "name": "G",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    h: None | str = field(
        default=None,
        metadata={
            "name": "H",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    i: None | str = field(
        default=None,
        metadata={
            "name": "I",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CTR|CTR-)([0-9])+",
        },
    )
