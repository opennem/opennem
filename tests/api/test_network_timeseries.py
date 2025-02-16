"""
Unit tests for the network time series endpoint supporting multiple metrics.

Note: These tests are using live database requests.
A separate test database will be set up later.
"""

from fastapi.testclient import TestClient

from opennem.api.main import app  # Adjust the import according to your application structure

client = TestClient(app)


def test_single_metric_no_grouping():
    response = client.get(
        "/v4/data/network/TEST_NETWORK",
        params={
            "metrics": "energy",
            "interval": "1h",
            "date_start": "2024-01-01T00:00:00",
            "date_end": "2024-01-01T12:00:00",
            "primary_grouping": "network",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # Ensure that data is present and contains time series results
    assert "data" in data
    ts_data = data["data"]
    assert "results" in ts_data
    # For a single metric with no grouping, expect at least one time series result.
    assert len(ts_data["results"]) >= 1


def test_multiple_metrics_no_grouping():
    response = client.get(
        "/v4/data/network/TEST_NETWORK",
        params={
            "metrics": ["energy", "power"],
            "interval": "1h",
            "date_start": "2024-01-01T00:00:00",
            "date_end": "2024-01-01T12:00:00",
            "primary_grouping": "network",
        },
    )
    assert response.status_code == 200, response.text
    ts_data = response.json()["data"]
    result_names = [r["name"] for r in ts_data["results"]]
    # Expect separate time series for both energy and power
    assert any("energy" in name for name in result_names)
    assert any("power" in name for name in result_names)


def test_grouping_secondary():
    response = client.get(
        "/v4/data/network/TEST_NETWORK",
        params={
            "metrics": ["energy", "power"],
            "interval": "1h",
            "date_start": "2024-01-01T00:00:00",
            "date_end": "2024-01-01T12:00:00",
            "primary_grouping": "network",
            "secondary_grouping": "fueltech_group",
        },
    )
    assert response.status_code == 200, response.text
    ts_data = response.json()["data"]
    # Check that the results have grouping information (i.e. the result names or columns include the secondary grouping)
    for result in ts_data["results"]:
        # Either the result name includes a grouping prefix or the columns field is populated.
        assert result.get("columns") or "fueltech_group" in result["name"]


def test_invalid_date_range():
    # For example, assume that for 5‑minute intervals (INTERVAL) the maximum allowed range is 7 days.
    response = client.get(
        "/v4/data/network/TEST_NETWORK",
        params={
            "metrics": ["energy"],
            "interval": "5m",
            "date_start": "2024-01-01T00:00:00",
            "date_end": "2024-01-10T00:00:00",  # intentionally too long
            "primary_grouping": "network",
        },
    )
    assert response.status_code == 400
