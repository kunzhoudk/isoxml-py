from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.det import Det
from isoxml.models.base.v2.dpd import Dpd
from isoxml.models.base.v2.dpt import Dpt
from isoxml.models.base.v2.dvp import Dvp


@dataclass(kw_only=True)
class Dvc:
    """
    Device.

    :ivar det: DeviceElement
    :ivar dpt: DeviceProperty
    :ivar dpd: DeviceProcessData
    :ivar dvp: DeviceValuePresentation
    :ivar a: DeviceId
    :ivar b: DeviceDesignator
    :ivar c: DeviceSoftwareVersion
    :ivar d: WorkingSetMasterNAME
    :ivar e: DeviceSerialNumber
    :ivar f: DeviceStructureLabel
    :ivar g: DeviceLocalizationLabel
    """

    class Meta:
        name = "DVC"

    det: list[Det] = field(
        default_factory=list,
        metadata={
            "name": "DET",
            "type": "Element",
        },
    )
    dpt: list[Dpt] = field(
        default_factory=list,
        metadata={
            "name": "DPT",
            "type": "Element",
        },
    )
    dpd: list[Dpd] = field(
        default_factory=list,
        metadata={
            "name": "DPD",
            "type": "Element",
        },
    )
    dvp: list[Dvp] = field(
        default_factory=list,
        metadata={
            "name": "DVP",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DVC|DVC-)([0-9])+",
        }
    )
    b: None | str = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    c: None | str = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    d: bytes = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "length": 8,
            "format": "base16",
        }
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    f: str = field(
        metadata={
            "name": "F",
            "type": "Attribute",
            "length": 7,
            "pattern": r"((([0-9]|[A-E])([0-9]|[A-F]))|(F([0-9]|[A-E])))*",
            "format": "base16",
        }
    )
    g: str = field(
        metadata={
            "name": "G",
            "type": "Attribute",
            "length": 7,
            "pattern": r"FF((([0-9]|[A-E])([0-9]|[A-F]))|(F([0-9]|[A-E])))*",
            "format": "base16",
        }
    )
