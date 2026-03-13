"""
ISOBUS Data Dictionary Entity (DDEntity) model.

The ISOBUS standard defines a Data Dictionary (DD) that assigns a unique numeric ID (DDI)
to each type of process data (e.g., DDI 1 = "Setpoint Volume Per Area", DDI 6 = "Actual Volume Content").
Each DDI entry carries metadata such as name, unit, and bit resolution (scale factor).

Full registry: https://www.isobus.net/isobus/dDEntity

中文总体说明：
- 本模块用于表示和查询 ISOBUS 的 DDI（Data Dictionary Item，数据字典项）。
- DDI 是过程数据类型的唯一编号；同一个编号对应固定的名称、单位和分辨率（bitResolution）。
- 模块在导入时会加载内置 `ddi_entities.json`，并提供按整数 ID 或按 2 字节编码进行反查。
- `DDEntity` 是一个轻量数据对象，常用于在 ISOXML 解析/生成时完成 DDI 与元数据之间的转换。

如何更新 `ddi_entities.json`：
1. 进入更新脚本目录：`cd resources/ddi_update`
2. 执行抓取脚本：`python ddi_entities_updater.py`
3. 覆盖库内数据文件：`cp ddi_entities.json ../../isoxml/data/ddi_entities.json`

说明：
- 脚本会从 ISOBUS 官方导出地址抓取最新 DDI 定义。
- 建议更新后运行相关测试（如 `test/models/ddi_entities_test.py`）再提交。
"""

import json
from dataclasses import dataclass
from importlib import resources

# Load all DDI definitions from the bundled JSON file at module import time.
# The JSON keys are string DDI numbers; convert them to int for direct lookup.
# Example entry: {1: {"DDI": 1, "name": "Setpoint Volume Per Area", "unit": "ml/m²", "bitResolution": 0.01}}
with resources.open_text("isoxml.data", "ddi_entities.json", encoding="utf-8") as file:
    _dd_entities = json.load(file)
_dd_entities = {int(k): v for k, v in _dd_entities.items()}


@dataclass
class DDEntity:
    """
    Represents a single ISOBUS Data Dictionary Entity.

    Attributes:
        ddi: The numeric DDI identifier (e.g., 1, 6).
        name: Human-readable name (e.g., "Setpoint Volume Per Area").
        unit: Physical unit string (e.g., "ml/m²"), or None if dimensionless.
        bit_resolution: Scale factor to convert raw integer values to real-world units.
                        e.g., 0.01 means raw value 100 → 1.0 in real units.
    """

    ddi: int
    name: str
    unit: str | None
    bit_resolution: float

    def __bytes__(self) -> bytes:
        """
        Python special method used by ``bytes(obj)``.

        Serialize the DDI number to 2 bytes in big-endian order,
        matching the ISOXML binary format for ProcessDataVariable DDI fields.

        Example: DDI 1 → b'\\x00\\x01', DDI 256 → b'\\x01\\x00'
        """
        return self.ddi.to_bytes(length=2, byteorder="big")

    @staticmethod
    def from_id(ddi: int):
        """
        Look up a DDEntity by its numeric DDI identifier from the preloaded JSON dictionary.

        Example: DDEntity.from_id(1) → DDEntity(ddi=1, name="Setpoint Volume Per Area", ...)
        """
        ddi_dict = _dd_entities[ddi]
        return DDEntity(
            ddi=ddi_dict["DDI"],
            name=ddi_dict["name"],
            unit=ddi_dict.get("unit"),
            bit_resolution=ddi_dict["bitResolution"],
        )

    @staticmethod
    def from_bytes(ddi_bytes: bytes):
        """
        Deserialize a 2-byte big-endian DDI field back into a DDEntity.
        Used when parsing ISOXML binary files.

        Example: DDEntity.from_bytes(b'\\x00\\x01') → DDEntity(ddi=1, ...)
        """
        return DDEntity.from_id(int.from_bytes(ddi_bytes, byteorder="big"))
