import json
from pathlib import Path

import pytest

from opennem.api.stats.schema import OpennemData
from opennem.core.flows import FlowDirection, fueltech_to_flow, generated_flow_station_id, invert_flow_set
from opennem.schema.network import NetworkNEM, NetworkRegionSchema, NetworkSchema

NSW1 = NetworkRegionSchema(code="NSW1", network_id="NEM")
VIC1 = NetworkRegionSchema(code="VIC1", network_id="NEM")


def get_power_flow_fixture() -> OpennemData:
    fixture_file = "power_flow_set.json"
    fixture_path = Path(__file__).parent / "fixtures" / fixture_file
    with fixture_path.open() as fh:
        fixture_envelope = json.load(fh)

    return OpennemData(**fixture_envelope)


@pytest.mark.parametrize(
    ["network", "network_region", "flow_direction", "code_expected"],
    [
        (NetworkNEM, NSW1, None, "NEM_FLOW_NSW1"),
        (NetworkNEM, VIC1, None, "NEM_FLOW_VIC1"),
        (NetworkNEM, NSW1, FlowDirection.imports, "NEM_FLOW_NSW1_IMPORTS"),
        (NetworkNEM, NSW1, FlowDirection.exports, "NEM_FLOW_NSW1_EXPORTS"),
    ],
)
def test_generated_flow_station_id(
    network: NetworkSchema,
    network_region: NetworkRegionSchema,
    flow_direction: FlowDirection,
    code_expected: str,
) -> None:
    code = generated_flow_station_id(network=network, network_region=network_region, flow_direction=flow_direction)
    assert code == code_expected, "Code return matches"


@pytest.mark.parametrize(
    ["fueltech_id", "flow_expected"],
    [
        ("imports", FlowDirection.imports),
        ("exports", FlowDirection.exports),
        ("coal_black", None),
    ],
)
def test_fueltech_to_flow(fueltech_id: str, flow_expected: FlowDirection) -> None:
    flow_direction = fueltech_to_flow(fueltech_id)

    assert flow_direction == flow_expected, "Got the expected flow"


def test_fixture_invert_flow() -> None:
    fixture = get_power_flow_fixture()
    inverted = invert_flow_set(fixture)

    assert "SA1->VIC1" in inverted.id, "id changed correctly"
    assert inverted.history.data[0] == -157.3, "data point 1 inverted"
    assert inverted.history.data[1] == 144.9, "data point 2 inverted"
