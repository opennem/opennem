import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opennem.api.app import app
from opennem.db import get_scoped_session
from opennem.db.models.opennem import Base, Network, NetworkRegion

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_scoped_session] = override_get_db

# Create a test client
client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Add test data
    wem = Network(code="WEM", country="au", label="WEM", timezone="Australia/Perth", interval_size=30)
    wem_region = NetworkRegion(network_id="WEM", code="WEM")
    nem = Network(code="NEM", country="au", label="NEM", timezone="Australia/Sydney", interval_size=5)
    nem_regions = [
        NetworkRegion(network_id="NEM", code="SA1"),
        NetworkRegion(network_id="NEM", code="TAS1"),
        NetworkRegion(network_id="NEM", code="VIC1"),
        NetworkRegion(network_id="NEM", code="QLD1"),
        NetworkRegion(network_id="NEM", code="NSW1"),
    ]
    db.add_all([wem, wem_region, nem] + nem_regions)
    db.commit()

    yield db

    Base.metadata.drop_all(bind=engine)


def test_app_startup(test_db):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == '"OK"'


def test_networks_endpoint(test_db):
    response = client.get("/networks")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2  # WEM and NEM

    # Check WEM
    wem = next(network for network in data if network["code"] == "WEM")
    assert wem["country"] == "au"
    assert wem["label"] == "WEM"
    assert wem["regions"] == [{"code": "WEM"}]
    assert wem["timezone"] == "Australia/Perth"
    assert wem["interval_size"] == 30

    # Check NEM
    nem = next(network for network in data if network["code"] == "NEM")
    assert nem["country"] == "au"
    assert nem["label"] == "NEM"
    assert {region["code"] for region in nem["regions"]} == {"SA1", "TAS1", "VIC1", "QLD1", "NSW1"}
    assert nem["timezone"] == "Australia/Sydney"
    assert nem["interval_size"] == 5
