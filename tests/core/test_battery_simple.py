"""
Simple test to verify the battery detection logic works.

This test focuses on the core logic rather than complex database mocking.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from opennem.core.battery import BatteryUnitMap


@pytest.mark.asyncio
async def test_battery_detection_integration():
    """Integration test for battery detection with simplified mocking."""

    # Mock battery unit map
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}

    # Mock database session and results
    mock_session = AsyncMock()

    # Mock the execute method to return proper results
    mock_result = AsyncMock()
    mock_result.fetchall.return_value = [
        (datetime(2024, 1, 1, 12, 0), -50.0),  # Charging interval - needs LVESL1 record
        (datetime(2024, 1, 1, 12, 5), 75.0),  # Discharging interval - needs LVESG1 record
    ]

    # Mock for split record checks - return None (no records found)
    mock_split_result = AsyncMock()
    mock_split_result.fetchone.return_value = None

    # Setup execute to return different results based on query
    async def mock_execute(query, params=None):
        if params and "bidirectional_unit" in params:
            return mock_result
        else:
            return mock_split_result

    mock_session.execute.side_effect = mock_execute

    with patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
        mock_get_map.return_value = battery_map

        with patch("opennem.core.battery.get_read_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            from opennem.core.battery import check_unsplit_batteries

            unsplit_units = await check_unsplit_batteries()

            # Should detect LVES1 as needing splitting
            assert "LVES1" in unsplit_units
            assert len(unsplit_units) == 1


@pytest.mark.asyncio
async def test_battery_detection_with_existing_records():
    """Test that units with existing split records are not flagged."""

    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}

    mock_session = AsyncMock()

    # Mock bidirectional records
    mock_result = AsyncMock()
    mock_result.fetchall.return_value = [
        (datetime(2024, 1, 1, 12, 0), -50.0),  # Charging
    ]

    # Mock split record exists
    mock_split_result = AsyncMock()
    mock_split_result.fetchone.return_value = (1,)  # Record exists

    async def mock_execute(query, params=None):
        if params and "bidirectional_unit" in params:
            return mock_result
        else:
            return mock_split_result

    mock_session.execute.side_effect = mock_execute

    with patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as mock_get_map:
        mock_get_map.return_value = battery_map

        with patch("opennem.core.battery.get_read_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            from opennem.core.battery import check_unsplit_batteries

            unsplit_units = await check_unsplit_batteries()

            # Should not detect any units (split records exist)
            assert len(unsplit_units) == 0


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_battery_detection_integration())
    print("✅ Battery detection test passed!")
