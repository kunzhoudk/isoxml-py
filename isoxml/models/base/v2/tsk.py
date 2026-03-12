from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.can import Can
from isoxml.models.base.v2.cnn import Cnn
from isoxml.models.base.v2.dan import Dan
from isoxml.models.base.v2.dlt import Dlt
from isoxml.models.base.v2.grd import Grd
from isoxml.models.base.v2.otp import Otp
from isoxml.models.base.v2.pan import Pan
from isoxml.models.base.v2.tim import Tim
from isoxml.models.base.v2.tlg import Tlg
from isoxml.models.base.v2.tsk_g import TskG
from isoxml.models.base.v2.tzn import Tzn
from isoxml.models.base.v2.wan import Wan


@dataclass(kw_only=True)
class Tsk:
    """
    Task.

    :ivar cnn: Connection
    :ivar dan: DeviceAllocation
    :ivar dlt: DataLogTrigger
    :ivar grd: Grid
    :ivar otp: OperTechPractice
    :ivar pan: ProductAllocation
    :ivar tim: Time
    :ivar tlg: TimeLog
    :ivar tzn: TreatmentZone
    :ivar wan: WorkerAllocation
    :ivar can: CommentAllocation
    :ivar a: TaskId
    :ivar b: TaskDesignator
    :ivar c: CustomerIdRef
    :ivar d: FarmIdRef
    :ivar e: PartfieldIdRef
    :ivar f: ResponsibleWorkerIdRef
    :ivar g: TaskStatus
    :ivar h: DefaultTreatmentZoneCode
    :ivar i: PositionLostTreatmentZoneCode
    :ivar j: OutOfFieldTreatmentZoneCode
    """

    class Meta:
        name = "TSK"

    cnn: list[Cnn] = field(
        default_factory=list,
        metadata={
            "name": "CNN",
            "type": "Element",
        },
    )
    dan: list[Dan] = field(
        default_factory=list,
        metadata={
            "name": "DAN",
            "type": "Element",
        },
    )
    dlt: list[Dlt] = field(
        default_factory=list,
        metadata={
            "name": "DLT",
            "type": "Element",
        },
    )
    grd: list[Grd] = field(
        default_factory=list,
        metadata={
            "name": "GRD",
            "type": "Element",
        },
    )
    otp: list[Otp] = field(
        default_factory=list,
        metadata={
            "name": "OTP",
            "type": "Element",
        },
    )
    pan: list[Pan] = field(
        default_factory=list,
        metadata={
            "name": "PAN",
            "type": "Element",
        },
    )
    tim: list[Tim] = field(
        default_factory=list,
        metadata={
            "name": "TIM",
            "type": "Element",
        },
    )
    tlg: list[Tlg] = field(
        default_factory=list,
        metadata={
            "name": "TLG",
            "type": "Element",
        },
    )
    tzn: list[Tzn] = field(
        default_factory=list,
        metadata={
            "name": "TZN",
            "type": "Element",
        },
    )
    wan: list[Wan] = field(
        default_factory=list,
        metadata={
            "name": "WAN",
            "type": "Element",
        },
    )
    can: list[Can] = field(
        default_factory=list,
        metadata={
            "name": "CAN",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(TSK|TSK-)([0-9])+",
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
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CTR|CTR-)([0-9])+",
        },
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(FRM|FRM-)([0-9])+",
        },
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PFD|PFD-)([0-9])+",
        },
    )
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(WKR|WKR-)([0-9])+",
        },
    )
    g: TskG = field(
        metadata={
            "name": "G",
            "type": "Attribute",
        }
    )
    h: None | int = field(
        default=None,
        metadata={
            "name": "H",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
    i: None | int = field(
        default=None,
        metadata={
            "name": "I",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
    j: None | int = field(
        default=None,
        metadata={
            "name": "J",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
