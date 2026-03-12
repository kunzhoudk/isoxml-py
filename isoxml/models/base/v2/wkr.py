from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Wkr:
    """
    Worker.

    :ivar a: WorkerId
    :ivar b: WorkerDesignator
    :ivar c: WorkerFirstName
    :ivar d: WorkerStreet
    :ivar e: WorkerPOBox
    :ivar f: WorkerPostalCode
    :ivar g: WorkerCity
    :ivar h: WorkerState
    :ivar i: WorkerCountry
    :ivar j: WorkerPhone
    :ivar k: WorkerMobile
    :ivar l: WorkerLicenseNumber
    :ivar m: WorkerEMail
    """

    class Meta:
        name = "WKR"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(WKR|WKR-)([0-9])+",
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
            "max_length": 32,
        },
    )
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "max_length": 10,
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
            "max_length": 32,
        },
    )
    j: None | str = field(
        default=None,
        metadata={
            "name": "J",
            "type": "Attribute",
            "max_length": 20,
        },
    )
    k: None | str = field(
        default=None,
        metadata={
            "name": "K",
            "type": "Attribute",
            "max_length": 20,
        },
    )
    l: None | str = field(
        default=None,
        metadata={
            "name": "L",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    m: None | str = field(
        default=None,
        metadata={
            "name": "M",
            "type": "Attribute",
            "max_length": 64,
        },
    )
