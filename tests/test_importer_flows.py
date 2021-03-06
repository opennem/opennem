import pytest

from opennem.core.networks import get_network_region_schema
from opennem.importer.trading_flows import FlowDirection, generated_flow_station_id
from opennem.schema.network import NetworkNEM, NetworkRegionSchema, NetworkSchema

NSW1 = get_network_region_schema(NetworkNEM, "NSW1").pop()
VIC1 = get_network_region_schema(NetworkNEM, "VIC1").pop()


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
