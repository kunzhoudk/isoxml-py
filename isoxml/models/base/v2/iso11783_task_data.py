from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.ccg import Ccg
from isoxml.models.base.v2.cct import Cct
from isoxml.models.base.v2.cld import Cld
from isoxml.models.base.v2.cpc import Cpc
from isoxml.models.base.v2.ctp import Ctp
from isoxml.models.base.v2.ctr import Ctr
from isoxml.models.base.v2.dvc import Dvc
from isoxml.models.base.v2.frm import Frm
from isoxml.models.base.v2.iso11783_task_data_data_transfer_origin import (
    Iso11783TaskDataDataTransferOrigin,
)
from isoxml.models.base.v2.iso11783_task_data_version_major import (
    Iso11783TaskDataVersionMajor,
)
from isoxml.models.base.v2.otq import Otq
from isoxml.models.base.v2.pdt import Pdt
from isoxml.models.base.v2.pfd import Pfd
from isoxml.models.base.v2.pgp import Pgp
from isoxml.models.base.v2.tsk import Tsk
from isoxml.models.base.v2.vpn import Vpn
from isoxml.models.base.v2.wkr import Wkr
from isoxml.models.base.v2.xfr import Xfr


@dataclass(kw_only=True)
class Iso11783TaskData:
    """
    ISO 11783 Task Data File Version 2.

    :ivar ccg: CodedCommentGroup
    :ivar cct: CodedComment
    :ivar cld: ColourLegend
    :ivar cpc: CulturalPractice
    :ivar ctp: CropType
    :ivar ctr: Customer
    :ivar dvc: Device
    :ivar frm: Farm
    :ivar otq: OperationTechnique
    :ivar pdt: Product
    :ivar pfd: Partfield
    :ivar pgp: ProductGroup
    :ivar tsk: Task
    :ivar vpn: ValuePresentation
    :ivar wkr: Worker
    :ivar xfr: ExternalFileReference
    :ivar version_major:
    :ivar version_minor:
    :ivar management_software_manufacturer:
    :ivar management_software_version:
    :ivar task_controller_manufacturer:
    :ivar task_controller_version:
    :ivar data_transfer_origin:
    """

    class Meta:
        name = "ISO11783_TaskData"

    ccg: list[Ccg] = field(
        default_factory=list,
        metadata={
            "name": "CCG",
            "type": "Element",
        },
    )
    cct: list[Cct] = field(
        default_factory=list,
        metadata={
            "name": "CCT",
            "type": "Element",
        },
    )
    cld: list[Cld] = field(
        default_factory=list,
        metadata={
            "name": "CLD",
            "type": "Element",
        },
    )
    cpc: list[Cpc] = field(
        default_factory=list,
        metadata={
            "name": "CPC",
            "type": "Element",
        },
    )
    ctp: list[Ctp] = field(
        default_factory=list,
        metadata={
            "name": "CTP",
            "type": "Element",
        },
    )
    ctr: list[Ctr] = field(
        default_factory=list,
        metadata={
            "name": "CTR",
            "type": "Element",
        },
    )
    dvc: list[Dvc] = field(
        default_factory=list,
        metadata={
            "name": "DVC",
            "type": "Element",
        },
    )
    frm: list[Frm] = field(
        default_factory=list,
        metadata={
            "name": "FRM",
            "type": "Element",
        },
    )
    otq: list[Otq] = field(
        default_factory=list,
        metadata={
            "name": "OTQ",
            "type": "Element",
        },
    )
    pdt: list[Pdt] = field(
        default_factory=list,
        metadata={
            "name": "PDT",
            "type": "Element",
        },
    )
    pfd: list[Pfd] = field(
        default_factory=list,
        metadata={
            "name": "PFD",
            "type": "Element",
        },
    )
    pgp: list[Pgp] = field(
        default_factory=list,
        metadata={
            "name": "PGP",
            "type": "Element",
        },
    )
    tsk: list[Tsk] = field(
        default_factory=list,
        metadata={
            "name": "TSK",
            "type": "Element",
        },
    )
    vpn: list[Vpn] = field(
        default_factory=list,
        metadata={
            "name": "VPN",
            "type": "Element",
        },
    )
    wkr: list[Wkr] = field(
        default_factory=list,
        metadata={
            "name": "WKR",
            "type": "Element",
        },
    )
    xfr: list[Xfr] = field(
        default_factory=list,
        metadata={
            "name": "XFR",
            "type": "Element",
        },
    )
    version_major: Iso11783TaskDataVersionMajor = field(
        metadata={
            "name": "VersionMajor",
            "type": "Attribute",
        }
    )
    version_minor: str = field(
        metadata={
            "name": "VersionMinor",
            "type": "Attribute",
            "min_length": 1,
        }
    )
    management_software_manufacturer: str = field(
        metadata={
            "name": "ManagementSoftwareManufacturer",
            "type": "Attribute",
            "max_length": 32,
        }
    )
    management_software_version: str = field(
        metadata={
            "name": "ManagementSoftwareVersion",
            "type": "Attribute",
            "max_length": 32,
        }
    )
    task_controller_manufacturer: None | str = field(
        default=None,
        metadata={
            "name": "TaskControllerManufacturer",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    task_controller_version: None | str = field(
        default=None,
        metadata={
            "name": "TaskControllerVersion",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    data_transfer_origin: Iso11783TaskDataDataTransferOrigin = field(
        metadata={
            "name": "DataTransferOrigin",
            "type": "Attribute",
        }
    )
