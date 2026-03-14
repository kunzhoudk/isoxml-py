"""Tests for isoxml.grid.convert – Grid Type 1 ↔ Type 2 conversion."""

import struct

import numpy as np
import pytest

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.grid.convert import grid_type1_to_type2, grid_type2_to_type1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_grid_v3(rows: int, cols: int, gtype: iso3.GridType, tzn_code=None) -> iso3.Grid:
    return iso3.Grid(
        maximum_row=rows,
        maximum_column=cols,
        type=gtype,
        treatment_zone_code=tzn_code,
        filename="GRD00001",
    )


def _make_grid_v4(rows: int, cols: int, gtype: iso4.GridType, tzn_code=None) -> iso4.Grid:
    return iso4.Grid(
        maximum_row=rows,
        maximum_column=cols,
        type=gtype,
        treatment_zone_code=tzn_code,
        filename="GRD00001",
    )


def _tzn3(code: int, pdv_values: list[int], ddi: bytes = b"\x00\x06") -> iso3.TreatmentZone:
    pdvs = [
        iso3.ProcessDataVariable(process_data_ddi=ddi, process_data_value=v)
        for v in pdv_values
    ]
    return iso3.TreatmentZone(code=code, process_data_variables=pdvs)


def _tzn4(code: int, pdv_values: list[int], ddi: bytes = b"\x00\x06") -> iso4.TreatmentZone:
    pdvs = [
        iso4.ProcessDataVariable(process_data_ddi=ddi, process_data_value=v)
        for v in pdv_values
    ]
    return iso4.TreatmentZone(code=code, process_data_variables=pdvs)


def _task3(*tzns: iso3.TreatmentZone) -> iso3.Task:
    return iso3.Task(id="TSK1", status=iso3.TaskStatus.Initial, treatment_zones=list(tzns))


def _task4(*tzns: iso4.TreatmentZone) -> iso4.Task:
    return iso4.Task(id="TSK1", status=iso4.TaskStatus.Planned, treatment_zones=list(tzns))


def _pack_int32(*values: int) -> bytes:
    return struct.pack(f"<{len(values)}i", *values)


# ---------------------------------------------------------------------------
# grid_type1_to_type2 – happy paths
# ---------------------------------------------------------------------------

class TestType1ToType2:

    def test_single_pdv_v3(self):
        """2×2 grid, two zones, single PDV each → int32 BIN."""
        tzn0 = _tzn3(0, [100])
        tzn1 = _tzn3(1, [200])
        task = _task3(tzn0, tzn1)

        # Zone codes: [[0, 1], [1, 0]]
        bin1 = bytes([0, 1, 1, 0])
        grid = _make_grid_v3(2, 2, iso3.GridType.GridType1)

        new_bin, new_grid = grid_type1_to_type2(bin1, grid, task)

        expected = _pack_int32(100, 200, 200, 100)
        assert new_bin == expected
        assert new_grid.type == iso3.GridType.GridType2

    def test_single_pdv_v4(self):
        """Same as above but with v4 objects."""
        tzn0 = _tzn4(0, [10])
        tzn1 = _tzn4(1, [20])
        task = _task4(tzn0, tzn1)

        bin1 = bytes([1, 0, 0, 1])
        grid = _make_grid_v4(2, 2, iso4.GridType.GridType1)

        new_bin, new_grid = grid_type1_to_type2(bin1, grid, task)

        expected = _pack_int32(20, 10, 10, 20)
        assert new_bin == expected
        assert new_grid.type == iso4.GridType.GridType2

    def test_multi_pdv(self):
        """3 zones × 2 PDVs each, 2×3 grid."""
        tzn0 = _tzn3(0, [0, 0])
        tzn1 = _tzn3(1, [10, -10])
        tzn2 = _tzn3(2, [20, -20])
        task = _task3(tzn0, tzn1, tzn2)

        # Zone codes row-major: 0, 1, 2, 2, 1, 0
        bin1 = bytes([0, 1, 2, 2, 1, 0])
        grid = _make_grid_v3(2, 3, iso3.GridType.GridType1)

        new_bin, new_grid = grid_type1_to_type2(bin1, grid, task)

        expected = _pack_int32(0, 0, 10, -10, 20, -20, 20, -20, 10, -10, 0, 0)
        assert new_bin == expected
        assert new_grid.type == iso3.GridType.GridType2

    def test_grid_type_is_not_mutated(self):
        """Original grid object must not be modified."""
        tzn = _tzn3(0, [1])
        task = _task3(tzn)
        bin1 = bytes([0, 0])
        grid = _make_grid_v3(1, 2, iso3.GridType.GridType1)

        _, new_grid = grid_type1_to_type2(bin1, grid, task)

        assert grid.type == iso3.GridType.GridType1  # original unchanged
        assert new_grid.type == iso3.GridType.GridType2

    # --- error cases ---

    def test_wrong_grid_type_raises(self):
        task = _task3(_tzn3(0, [0]))
        grid = _make_grid_v3(1, 1, iso3.GridType.GridType2)
        with pytest.raises(ValueError, match="GridType1"):
            grid_type1_to_type2(bytes([0]), grid, task)

    def test_no_treatment_zones_raises(self):
        task = _task3()
        grid = _make_grid_v3(1, 1, iso3.GridType.GridType1)
        with pytest.raises(ValueError, match="no TreatmentZones"):
            grid_type1_to_type2(bytes([0]), grid, task)

    def test_missing_zone_code_raises(self):
        """A code in the BIN that has no matching TZN must raise."""
        tzn0 = _tzn3(0, [0])
        task = _task3(tzn0)  # only zone 0 defined
        bin1 = bytes([0, 1])  # zone 1 missing
        grid = _make_grid_v3(1, 2, iso3.GridType.GridType1)
        with pytest.raises(ValueError, match="Zone code"):
            grid_type1_to_type2(bin1, grid, task)

    def test_inconsistent_pdv_count_raises(self):
        """Zones with different PDV counts must raise."""
        tzn0 = _tzn3(0, [1])
        tzn1 = _tzn3(1, [2, 3])  # extra PDV
        task = _task3(tzn0, tzn1)
        bin1 = bytes([0, 1])
        grid = _make_grid_v3(1, 2, iso3.GridType.GridType1)
        with pytest.raises(ValueError, match="PDV count"):
            grid_type1_to_type2(bin1, grid, task)


# ---------------------------------------------------------------------------
# grid_type2_to_type1 – happy paths
# ---------------------------------------------------------------------------

class TestType2ToType1:

    def test_single_pdv_v3(self):
        """2×2 grid, two unique values → 2 zones."""
        # Values: [[100, 200], [200, 100]]
        bin2 = _pack_int32(100, 200, 200, 100)
        grid = _make_grid_v3(2, 2, iso3.GridType.GridType2)
        task = _task3()  # no TZNs needed for conversion (no DDI template)

        new_bin, new_grid, new_tzns = grid_type2_to_type1(bin2, grid, task)

        assert new_grid.type == iso3.GridType.GridType1
        assert new_grid.treatment_zone_code is None

        # Decode zone codes
        codes = np.frombuffer(new_bin, dtype=np.uint8).reshape(2, 2)
        # Unique values in row-major order: 100 and 200
        # np.unique returns them sorted: [100, 200]
        assert codes[0, 0] == codes[1, 1]   # both 100 → same zone
        assert codes[0, 1] == codes[1, 0]   # both 200 → same zone
        assert codes[0, 0] != codes[0, 1]

        assert len(new_tzns) == 2
        zone_values = {tzn.code: tzn.process_data_variables[0].process_data_value
                       for tzn in new_tzns}
        # Zones 0 and 1; sorted unique values are [100, 200]
        assert set(zone_values.values()) == {100, 200}

    def test_single_pdv_v4(self):
        bin2 = _pack_int32(5, 5, 5, 10)
        grid = _make_grid_v4(2, 2, iso4.GridType.GridType2)
        task = _task4()

        new_bin, new_grid, new_tzns = grid_type2_to_type1(bin2, grid, task)

        assert new_grid.type == iso4.GridType.GridType1
        assert len(new_tzns) == 2  # {5, 10}
        assert all(isinstance(t, iso4.TreatmentZone) for t in new_tzns)

    def test_multi_pdv(self):
        """2×2 grid with 2 PDVs per cell → 3 unique combinations."""
        # Cell values (row-major): (0,0), (1,-1), (0,0), (2,-2)
        bin2 = _pack_int32(0, 0, 1, -1, 0, 0, 2, -2)
        grid = _make_grid_v3(2, 2, iso3.GridType.GridType2)
        task = _task3()

        new_bin, new_grid, new_tzns = grid_type2_to_type1(bin2, grid, task)

        codes = np.frombuffer(new_bin, dtype=np.uint8).reshape(2, 2)
        # Cells (0,0) and (1,0) are identical → same zone code
        assert codes[0, 0] == codes[1, 0]
        # All three unique value pairs present
        assert len(new_tzns) == 3
        for tzn in new_tzns:
            assert len(tzn.process_data_variables) == 2

    def test_ddi_inherited_from_template_tzn(self):
        """DDI and refs must be copied from the template TreatmentZone."""
        ddi = b"\x00\x01"
        template = iso3.TreatmentZone(
            code=7,
            process_data_variables=[
                iso3.ProcessDataVariable(
                    process_data_ddi=ddi,
                    process_data_value=999,
                    product_id_ref="PDT1",
                )
            ],
        )
        task = _task3(template)
        bin2 = _pack_int32(10, 20)
        grid = _make_grid_v3(1, 2, iso3.GridType.GridType2, tzn_code=7)

        _, _, new_tzns = grid_type2_to_type1(bin2, grid, task)

        for tzn in new_tzns:
            assert tzn.process_data_variables[0].process_data_ddi == ddi
            assert tzn.process_data_variables[0].product_id_ref == "PDT1"

    def test_all_cells_same_value(self):
        """Single unique value → single zone, all cells reference it."""
        bin2 = _pack_int32(42, 42, 42, 42)
        grid = _make_grid_v3(2, 2, iso3.GridType.GridType2)
        task = _task3()

        new_bin, _, new_tzns = grid_type2_to_type1(bin2, grid, task)

        codes = np.frombuffer(new_bin, dtype=np.uint8)
        assert np.all(codes == codes[0])
        assert len(new_tzns) == 1
        assert new_tzns[0].process_data_variables[0].process_data_value == 42

    def test_grid_type_not_mutated(self):
        bin2 = _pack_int32(1, 2)
        grid = _make_grid_v3(1, 2, iso3.GridType.GridType2)
        task = _task3()

        _, new_grid, _ = grid_type2_to_type1(bin2, grid, task)

        assert grid.type == iso3.GridType.GridType2
        assert new_grid.type == iso3.GridType.GridType1

    # --- error cases ---

    def test_wrong_grid_type_raises(self):
        grid = _make_grid_v3(1, 1, iso3.GridType.GridType1)
        with pytest.raises(ValueError, match="GridType2"):
            grid_type2_to_type1(bytes([0]), grid, _task3())

    def test_too_many_unique_values_raises(self):
        """256 distinct int32 values → exceeds 254-zone limit."""
        values = list(range(256))
        bin2 = struct.pack(f"<{len(values)}i", *values)
        grid = _make_grid_v3(1, 256, iso3.GridType.GridType2)
        with pytest.raises(ValueError, match="254 zones"):
            grid_type2_to_type1(bin2, grid, _task3())


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:

    def test_type1_to_type2_to_type1_v3(self):
        """Type 1 → Type 2 → Type 1 must recover original zone code layout."""
        tzn0 = _tzn3(0, [0])
        tzn1 = _tzn3(1, [100])
        tzn2 = _tzn3(2, [200])
        task = _task3(tzn0, tzn1, tzn2)

        # 2×3 grid with zone codes
        original_codes = np.array([[0, 1, 2], [2, 1, 0]], dtype=np.uint8)
        bin1 = original_codes.tobytes(order="C")
        grid = _make_grid_v3(2, 3, iso3.GridType.GridType1)

        bin2, grid2 = grid_type1_to_type2(bin1, grid, task)

        # Now convert back to Type 1; update task with new TZNs
        bin1b, grid1b, new_tzns = grid_type2_to_type1(bin2, grid2, task)
        task.treatment_zones = new_tzns

        # Re-convert back to Type 2 and check that PDV values are preserved
        bin2b, _ = grid_type1_to_type2(bin1b, grid1b, task)

        # Decode both Type 2 BINs and compare PDV values
        vals_a = np.frombuffer(bin2, dtype=np.int32)
        vals_b = np.frombuffer(bin2b, dtype=np.int32)
        assert np.array_equal(vals_a, vals_b)

    def test_type2_to_type1_and_back_multi_pdv(self):
        """Type 2 (multi-PDV) → Type 1 → Type 2 must preserve all values."""
        # 2×2 grid, 2 PDVs: unique pairs (1,2), (3,4)
        bin2_orig = _pack_int32(1, 2, 3, 4, 3, 4, 1, 2)
        grid2 = _make_grid_v3(2, 2, iso3.GridType.GridType2)
        task = _task3()

        bin1, grid1, new_tzns = grid_type2_to_type1(bin2_orig, grid2, task)
        task.treatment_zones = new_tzns

        bin2_back, _ = grid_type1_to_type2(bin1, grid1, task)

        vals_orig = np.frombuffer(bin2_orig, dtype=np.int32).reshape(2, 2, 2)
        vals_back = np.frombuffer(bin2_back, dtype=np.int32).reshape(2, 2, 2)
        assert np.array_equal(vals_orig, vals_back)
