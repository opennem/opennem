"""
Tests for the network data API endpoints.

This module tests various combinations of metrics, intervals, and groupings
for the network data endpoints.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from opennem.api.app import app
from opennem.core.time_interval import Interval


@pytest.fixture
def client():
    """Get a TestClient instance."""
    return TestClient(app)


@pytest.fixture
def recent_date_range():
    """Get a recent date range for testing."""
    end = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    return start, end


def test_get_network_data_single_metric(client, recent_date_range):
    """Test getting a single metric with default settings."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1  # One metric
    assert data[0]["metric"] == "energy"
    assert data[0]["network_code"] == "NEM"
    assert data[0]["interval"] == Interval.INTERVAL.value
    assert len(data[0]["results"]) == 1  # One result for network total
    assert data[0]["results"][0]["name"] == "NEM"
    assert len(data[0]["results"][0]["data"]) > 0


def test_get_network_data_multiple_metrics(client, recent_date_range):
    """Test getting multiple metrics in a single request."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": ["energy", "emissions"],
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2  # Two metrics
    metrics = {d["metric"] for d in data}
    assert metrics == {"energy", "emissions"}


def test_get_network_data_with_regions(client, recent_date_range):
    """Test getting data grouped by network regions."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "primary_grouping": "network_region",
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    results = data[0]["results"]
    assert len(results) > 1  # Multiple regions
    regions = {r["name"] for r in results}
    assert regions.issuperset({"NSW1", "QLD1", "VIC1", "SA1", "TAS1"})


def test_get_network_data_with_fueltech(client, recent_date_range):
    """Test getting data grouped by fueltech."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "primary_grouping": "network_region",
            "secondary_grouping": "fueltech",
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    results = data[0]["results"]
    assert len(results) > 0
    # Check that results include region and fueltech in names
    assert all("_" in r["name"] for r in results)
    assert all("fueltech_id" in r["columns"] for r in results)


def test_get_network_data_with_renewable(client, recent_date_range):
    """Test getting data grouped by renewable status."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "secondary_grouping": "renewable",
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    results = data[0]["results"]
    names = {r["name"] for r in results}
    assert names == {"renewable", "carbon"}


@pytest.mark.parametrize(
    "interval",
    [
        "5m",  # Default 5-minute intervals
        "1h",  # Hourly
        "1d",  # Daily
        "1M",  # Monthly
        "1y",  # Yearly
    ],
)
def test_get_network_data_intervals(client, recent_date_range, interval):
    """Test getting data with different time intervals."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "interval": interval,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["interval"] == interval


def test_get_network_data_all_metrics(client, recent_date_range):
    """Test getting all available metrics."""
    start, end = recent_date_range
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": ["energy", "emissions", "market_value", "power"],
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 4
    metrics = {d["metric"] for d in data}
    assert metrics == {"energy", "emissions", "market_value", "power"}


def test_get_network_data_invalid_metric(client):
    """Test error handling for invalid metrics."""
    response = client.get(
        "/v4/data/network/NEM",
        params={"metrics": "invalid_metric"},
    )
    assert response.status_code == 422  # Validation error


def test_get_network_data_invalid_network(client):
    """Test error handling for invalid network code."""
    response = client.get(
        "/v4/data/network/INVALID",
        params={"metrics": "energy"},
    )
    assert response.status_code == 404  # Not found


def test_get_network_data_invalid_date_range(client):
    """Test error handling for invalid date ranges."""
    response = client.get(
        "/v4/data/network/NEM",
        params={
            "metrics": "energy",
            "date_start": "2024-01-02T00:00:00",
            "date_end": "2024-01-01T00:00:00",  # End before start
        },
    )
    assert response.status_code == 400  # Bad request
