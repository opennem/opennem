from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import NetworkSchema

_NETWORK_REGION_NAME_MAP = {
    "QLD1": "Queensland",
    "NSW1": "New South Wales",
    "VIC1": "Victoria",
    "SA1": "South Australia",
    "TAS1": "Tasmania",
    "WEM": "Western Australia",
    "WEMDE": "Western Australia",
}


def get_network_region_name(network_region: str) -> str:
    """Return the name of a network region"""
    return _NETWORK_REGION_NAME_MAP.get(network_region, network_region)


def get_network_regions(network: NetworkSchema, network_region: str | None = None) -> list[NetworkRegion]:
    """Return regions for a network"""
    with SessionLocal() as s:
        regions = s.query(NetworkRegion).filter_by(network_id=network.code)

        if network_region:
            regions = regions.filter_by(code=network_region)

        regions = regions.all()

        return regions
