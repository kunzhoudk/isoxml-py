"""ISOBUS Data Dictionary Entity (DDEntity) model.

The ISOBUS standard assigns a unique numeric ID (DDI) to each type of process
data (e.g. DDI 1 = "Setpoint Volume Per Area", DDI 6 = "Actual Volume Content").
Each entry carries a name, physical unit, and bit resolution (scale factor).

Full registry: https://www.isobus.net/isobus/dDEntity

How to refresh ``ddi_entities.json``:
1. ``python -m isoxml.reference.update_ddi_registry``
2. Commit the updated ``src/isoxml/reference/ddi_entities.json``
"""

import json
from dataclasses import dataclass
from importlib import resources

# Load all DDI definitions from the bundled JSON file at import time.
# Keys are converted from strings to ints for direct O(1) lookup.
_json_ref = resources.files("isoxml.reference").joinpath("ddi_entities.json")
with _json_ref.open(encoding="utf-8") as _fh:
    _DD_REGISTRY: dict[int, dict] = {int(k): v for k, v in json.load(_fh).items()}


@dataclass
class DDEntity:
    """A single ISOBUS Data Dictionary Item.

    Attributes:
        ddi: Numeric DDI identifier (e.g. ``1``, ``6``).
        name: Human-readable name (e.g. ``"Setpoint Volume Per Area"``).
        unit: Physical unit string (e.g. ``"ml/m²"``), or ``None`` if
            dimensionless.
        bit_resolution: Scale factor converting raw integer values to
            real-world units.  Example: ``0.01`` means raw ``100`` → ``1.0``.
    """

    ddi: int
    name: str
    unit: str | None
    bit_resolution: float

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def __bytes__(self) -> bytes:
        """Serialize the DDI number to 2 bytes (big-endian).

        Matches the ISOXML binary encoding for ProcessDataVariable DDI fields.
        Example: DDI 1 → ``b'\\x00\\x01'``, DDI 256 → ``b'\\x01\\x00'``.
        """
        return self.ddi.to_bytes(length=2, byteorder="big")

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_id(ddi: int) -> "DDEntity":
        """Look up a ``DDEntity`` by its numeric DDI identifier.

        Raises:
            KeyError: If *ddi* is not present in the bundled registry.
        """
        entry = _DD_REGISTRY[ddi]
        return DDEntity(
            ddi=entry["DDI"],
            name=entry["name"],
            unit=entry.get("unit"),
            bit_resolution=entry["bitResolution"],
        )

    @staticmethod
    def from_bytes(ddi_bytes: bytes) -> "DDEntity":
        """Deserialize a 2-byte big-endian DDI field into a ``DDEntity``.

        Example: ``DDEntity.from_bytes(b'\\x00\\x01')`` → DDI 1.
        """
        return DDEntity.from_id(int.from_bytes(ddi_bytes, byteorder="big"))
