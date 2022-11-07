from datetime import datetime

from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import (
    NETWORKS,
    NetworkAPVI,
    NetworkAU,
    NetworkNEM,
    NetworkRegionSchema,
    NetworkSchema,
    NetworkWEM,
)

NEM_STATES = ["QLD", "NSW", "VIC", "ACT", "TAS", "SA", "NT"]


def state_from_network_region(network_region: str) -> str:
    _state = network_region

    if _state.endswith("1"):
        _state = _state[:-1]

    _state = _state.strip().upper()

    if _state in NEM_STATES:
        return _state

    raise Exception(f"State {network_region} not found")


def network_from_state(state: str) -> NetworkSchema:
    state = state.upper().strip()

    if state in ["WA"]:
        return NetworkWEM

    if state in ["QLD", "NSW", "VIC", "ACT", "TAS", "SA", "NT"]:
        return NetworkNEM

    raise Exception(f"Unknown network {state}")


def network_from_network_region(
    network_region: str,
) -> NetworkSchema:
    network_region = network_region.upper()

    if network_region in ["WEM", "WA1"]:
        return NetworkWEM
    if network_region in ["NEM", "NSW1", "QLD1", "SA1", "VIC1", "TAS1"]:
        return NetworkNEM

    raise Exception(f"Unknown network {network_region}")


def network_from_network_code(network_code: str) -> NetworkSchema:
    network_code = network_code.upper().strip()

    if network_code in ["AU"]:
        return NetworkAU

    if network_code in ["WEM"]:
        return NetworkWEM

    if network_code in ["NEM"]:
        return NetworkNEM

    if network_code in ["APVI"]:
        return NetworkAPVI

    network_lookup = list(filter(lambda n: n.code == network_code, NETWORKS))

    if len(network_lookup):
        return network_lookup.pop()

    raise Exception(f"Unknown network {network_code}")


def get_network_region_schema(network: NetworkSchema, network_region_code: str | None = None) -> list[NetworkRegionSchema]:
    """Return regions for a network"""
    s = SessionLocal()
    regions_query = s.query(NetworkRegion).filter_by(network_id=network.code)

    if network_region_code:
        regions_query = regions_query.filter_by(code=network_region_code)

    regions_result = regions_query.all()

    regions = [NetworkRegionSchema.from_orm(i) for i in regions_result]

    return regions


def datetime_add_network_timezone(dt: datetime, network: NetworkSchema) -> datetime:
    """Returns a datetime in network timezone"""
    return dt.astimezone(network.get_fixed_offset())
