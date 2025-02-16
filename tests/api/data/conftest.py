"""
Common test fixtures for API tests.

This module contains fixtures that can be used across all API tests.
"""

import pytest
from fastapi.testclient import TestClient

from opennem.api.app import app


@pytest.fixture
def client():
    """Get a TestClient instance."""
    return TestClient(app)


@pytest.fixture
def nem_network_code():
    """Get the NEM network code."""
    return "NEM"


@pytest.fixture
def wem_network_code():
    """Get the WEM network code."""
    return "WEM"


@pytest.fixture
def mock_network_regions():
    """Mock network regions data."""
    return [
        {"code": "NSW1", "timezone": "Australia/Sydney"},
        {"code": "QLD1", "timezone": "Australia/Brisbane"},
        {"code": "VIC1", "timezone": "Australia/Melbourne"},
        {"code": "SA1", "timezone": "Australia/Adelaide"},
        {"code": "TAS1", "timezone": "Australia/Hobart"},
    ]
