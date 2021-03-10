import pytest

from opennem.core.flows import FlowDirection, fueltech_to_flow, generated_flow_station_id
from opennem.schema.network import NetworkNEM, NetworkRegionSchema, NetworkSchema

NSW1 = NetworkRegionSchema(code="NSW1", network_id="NEM")
VIC1 = NetworkRegionSchema(code="VIC1", network_id="NEM")


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
    code = generated_flow_station_id(
        network=network, network_region=network_region, flow_direction=flow_direction
    )
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
