from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import NetworkSchema


def get_network_regions(network: NetworkSchema, network_region: str | None = None) -> list[NetworkRegion]:
    """Return regions for a network"""
    with SessionLocal() as s:
        regions = s.query(NetworkRegion).filter_by(network_id=network.code)

        if network_region:
            regions = regions.filter_by(code=network_region)

        regions = regions.all()

        return regions
