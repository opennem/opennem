"""
Unit tests for battery splitting functionality in NEM controller.

Tests verify that the generate_facility_scada function correctly:
1. Preserves original bidirectional battery records
2. Creates additional charge/discharge records for battery facilities
3. Leaves non-battery records unchanged
4. Applies correct transformations to battery generation values
"""

from unittest.mock import AsyncMock, patch

import pytest

from opennem.controllers.nem import generate_facility_scada
from opennem.core.networks import NetworkNEM


class TestNEMBatterySplitting:
    """Test battery splitting functionality in NEM controller."""

    @pytest.fixture
    def mock_battery_unit_map(self):
        """Mock battery unit mapping for testing."""
        from opennem.core.battery import BatteryUnitMap

        return {
            "LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1"),
            "TEMPB1": BatteryUnitMap(unit="TEMPB1", charge_unit="TEMPBL1", discharge_unit="TEMPBG1"),
        }

    @pytest.fixture
    def sample_records(self):
        """Sample input records for testing."""
        return [
            # Battery facility with negative generation (charging)
            {
                "settlementdate": "2024-01-01 12:00:00",
                "duid": "LVES1",
                "scadavalue": -50.0,
            },
            # Battery facility with positive generation (discharging)
            {
                "settlementdate": "2024-01-01 12:05:00",
                "duid": "LVES1",
                "scadavalue": 75.0,
            },
            # Non-battery facility
            {
                "settlementdate": "2024-01-01 12:00:00",
                "duid": "REGULAR_UNIT",
                "scadavalue": 100.0,
            },
            # Another battery facility with charging
            {
                "settlementdate": "2024-01-01 12:00:00",
                "duid": "TEMPB1",
                "scadavalue": -25.0,
            },
        ]

    @pytest.mark.asyncio
    async def test_battery_splitting_preserves_originals(self, mock_battery_unit_map, sample_records):
        """Test that original bidirectional battery records are preserved."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Find original battery records in results
            original_lves1_records = [r for r in result_records if r["facility_code"] == "LVES1"]
            original_tempb1_records = [r for r in result_records if r["facility_code"] == "TEMPB1"]

            # Should have both original LVES1 records
            assert len(original_lves1_records) == 2

            # Check negative generation record is preserved
            charging_record = next((r for r in original_lves1_records if r["generated"] == -50.0), None)
            assert charging_record is not None
            assert charging_record["generated"] == -50.0

            # Check positive generation record is preserved
            discharging_record = next((r for r in original_lves1_records if r["generated"] == 75.0), None)
            assert discharging_record is not None
            assert discharging_record["generated"] == 75.0

            # Should have original TEMPB1 record
            assert len(original_tempb1_records) == 1
            assert original_tempb1_records[0]["generated"] == -25.0

    @pytest.mark.asyncio
    async def test_battery_splitting_creates_split_records(self, mock_battery_unit_map, sample_records):
        """Test that additional charge/discharge records are created."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Find charge records (should be created for negative generation)
            charge_records = [r for r in result_records if r["facility_code"] in ["LVESL1", "TEMPBL1"]]

            # Find discharge records (should be created for positive generation)
            discharge_records = [r for r in result_records if r["facility_code"] in ["LVESG1", "TEMPBG1"]]

            # Should have charge records for negative generation
            assert len(charge_records) == 2  # LVES1 and TEMPB1 charging

            # Check LVES1 charge record
            lves1_charge = next((r for r in charge_records if r["facility_code"] == "LVESL1"), None)
            assert lves1_charge is not None
            assert lves1_charge["generated"] == 50.0  # Absolute value of -50

            # Check TEMPB1 charge record
            tempb1_charge = next((r for r in charge_records if r["facility_code"] == "TEMPBL1"), None)
            assert tempb1_charge is not None
            assert tempb1_charge["generated"] == 25.0  # Absolute value of -25

            # Should have discharge record for positive generation
            assert len(discharge_records) == 1  # Only LVES1 discharging

            # Check LVES1 discharge record
            lves1_discharge = discharge_records[0]
            assert lves1_discharge["facility_code"] == "LVESG1"
            assert lves1_discharge["generated"] == 75.0  # Unchanged positive value

    @pytest.mark.asyncio
    async def test_non_battery_records_unchanged(self, mock_battery_unit_map, sample_records):
        """Test that non-battery records are not affected by battery splitting."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Find non-battery records
            non_battery_records = [r for r in result_records if r["facility_code"] == "REGULAR_UNIT"]

            # Should have exactly one non-battery record
            assert len(non_battery_records) == 1

            # Should be unchanged
            record = non_battery_records[0]
            assert record["facility_code"] == "REGULAR_UNIT"
            assert record["generated"] == 100.0

    @pytest.mark.asyncio
    async def test_total_record_count_increases(self, mock_battery_unit_map, sample_records):
        """Test that total record count increases due to battery splitting."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Should have more output records than input records
            assert len(result_records) > len(sample_records)

            # Specifically: 4 input + 3 battery split records = 7 total
            # - LVES1 charging (-50) -> creates LVESL1 charge record
            # - LVES1 discharging (75) -> creates LVESG1 discharge record
            # - TEMPB1 charging (-25) -> creates TEMPBL1 charge record
            assert len(result_records) == 7

    @pytest.mark.asyncio
    async def test_energy_calculation_correct(self, mock_battery_unit_map, sample_records):
        """Test that energy values are calculated correctly for all records."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Check that all records have energy calculated
            for record in result_records:
                expected_energy = record["generated"] / (60 / NetworkNEM.interval_size)
                assert abs(record["energy"] - expected_energy) < 0.0001  # Float precision

            # Verify specific energy calculations
            # For 5-minute intervals: energy = generated / 12

            # Original LVES1 charging: -50 MW -> -4.167 MWh
            lves1_charge_orig = next(
                (r for r in result_records if r["facility_code"] == "LVES1" and r["generated"] == -50.0), None
            )
            assert lves1_charge_orig is not None
            assert abs(lves1_charge_orig["energy"] - (-50.0 / 12)) < 0.0001

            # Split LVES1 charge record: 50 MW -> 4.167 MWh
            lves1_charge_split = next((r for r in result_records if r["facility_code"] == "LVESL1"), None)
            assert lves1_charge_split is not None
            assert abs(lves1_charge_split["energy"] - (50.0 / 12)) < 0.0001

    @pytest.mark.asyncio
    async def test_empty_battery_map(self, sample_records):
        """Test behavior when no battery units are configured."""
        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = {}  # Empty battery map

            result_records = await generate_facility_scada(
                records=sample_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Should have same number of records as input (no splitting)
            assert len(result_records) == len(sample_records)

            # All facility codes should be unchanged
            input_facility_codes = {r["duid"] for r in sample_records}
            output_facility_codes = {r["facility_code"] for r in result_records}
            assert input_facility_codes == output_facility_codes

    @pytest.mark.asyncio
    async def test_zero_generation_handling(self, mock_battery_unit_map):
        """Test handling of zero generation values."""
        zero_gen_records = [
            {
                "settlementdate": "2024-01-01 12:00:00",
                "duid": "LVES1",
                "scadavalue": 0.0,
            }
        ]

        with patch("opennem.controllers.nem.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
            mock_get_map.return_value = mock_battery_unit_map

            result_records = await generate_facility_scada(
                records=zero_gen_records,
                network=NetworkNEM,
                interval_field="settlementdate",
                facility_code_field="duid",
                power_field="scadavalue",
            )

            # Should have original record plus discharge record (0 >= 0)
            assert len(result_records) == 2

            # Check original record
            original = next((r for r in result_records if r["facility_code"] == "LVES1"), None)
            assert original is not None
            assert original["generated"] == 0.0

            # Check discharge record
            discharge = next((r for r in result_records if r["facility_code"] == "LVESG1"), None)
            assert discharge is not None
            assert discharge["generated"] == 0.0
