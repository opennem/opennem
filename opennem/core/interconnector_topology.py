"""Dynamic interconnector topology loader.

Loads NEM interconnector topology from the units table instead of hardcoding.
Supports automatic expansion when new interconnectors (e.g. PEC NSW1<->SA1) appear.
"""

import logging
from dataclasses import dataclass, field
from functools import lru_cache

from opennem.db import db_connect_sync
from opennem.schema.network import NetworkNEM, NetworkSchema

logger = logging.getLogger("opennem.core.interconnector_topology")


@dataclass(frozen=True)
class NetworkTopology:
    """Interconnector topology for a network.

    Attributes:
        network: network schema
        regions: sorted list of region codes (e.g. ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"])
        flows: list of (region_from, region_to) directional pairs
    """

    network: NetworkSchema
    regions: tuple[str, ...] = field(default_factory=tuple)
    flows: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def region_index(self) -> dict[str, int]:
        """Map region code to matrix index."""
        return {r: i for i, r in enumerate(self.regions)}

    @property
    def flow_index(self) -> dict[tuple[str, str], int]:
        """Map (from, to) pair to flow index."""
        return {f: i for i, f in enumerate(self.flows)}

    @property
    def num_regions(self) -> int:
        return len(self.regions)

    @property
    def num_flows(self) -> int:
        return len(self.flows)

    def flows_into(self, region: str) -> list[tuple[str, str]]:
        """All flows where region is the destination."""
        return [(f, t) for f, t in self.flows if t == region]

    def flows_out_of(self, region: str) -> list[tuple[str, str]]:
        """All flows where region is the source."""
        return [(f, t) for f, t in self.flows if f == region]


def load_topology_from_db(network: NetworkSchema = NetworkNEM) -> NetworkTopology:
    """Load interconnector topology from PG units table.

    Queries distinct (interconnector_region_from, interconnector_region_to) pairs
    for units marked as interconnectors in the given network.
    """
    engine = db_connect_sync()

    query = f"""
        SELECT DISTINCT
            u.interconnector_region_from,
            u.interconnector_region_to
        FROM units u
        JOIN facilities f ON u.station_id = f.id
        WHERE u.interconnector = true
            AND f.network_id = '{network.code}'
            AND u.interconnector_region_from IS NOT NULL
            AND u.interconnector_region_to IS NOT NULL
        ORDER BY 1, 2
    """

    with engine.connect() as conn:
        result = conn.execute(__import__("sqlalchemy").text(query))
        rows = result.fetchall()

    if not rows:
        logger.warning(f"No interconnectors found for network {network.code}")
        return NetworkTopology(network=network)

    flows: list[tuple[str, str]] = [(row[0], row[1]) for row in rows]
    regions = sorted({r for pair in flows for r in pair})

    topology = NetworkTopology(
        network=network,
        regions=tuple(regions),
        flows=tuple(flows),
    )

    logger.info(f"Loaded topology for {network.code}: {topology.num_regions} regions, {topology.num_flows} directional flows")

    return topology


@lru_cache(maxsize=4)
def get_network_topology(network_code: str = "NEM") -> NetworkTopology:
    """Cached topology lookup. Call .cache_clear() to refresh after interconnector changes."""
    from opennem.schema.network import NETWORKS

    network = next((n for n in NETWORKS if n.code == network_code), None)
    if not network:
        raise ValueError(f"Unknown network: {network_code}")
    return load_topology_from_db(network)


# Hardcoded fallback for NEM (pre-PEC topology) used when DB is unavailable or in tests
NEM_DEFAULT_TOPOLOGY = NetworkTopology(
    network=NetworkNEM,
    regions=("NSW1", "QLD1", "SA1", "TAS1", "VIC1"),
    flows=(
        ("NSW1", "QLD1"),
        ("NSW1", "VIC1"),
        ("QLD1", "NSW1"),
        ("SA1", "VIC1"),
        ("TAS1", "VIC1"),
        ("VIC1", "NSW1"),
        ("VIC1", "SA1"),
        ("VIC1", "TAS1"),
    ),
)

# Post-PEC topology (for testing)
NEM_PEC_TOPOLOGY = NetworkTopology(
    network=NetworkNEM,
    regions=("NSW1", "QLD1", "SA1", "TAS1", "VIC1"),
    flows=(
        ("NSW1", "QLD1"),
        ("NSW1", "SA1"),  # PEC
        ("NSW1", "VIC1"),
        ("QLD1", "NSW1"),
        ("SA1", "NSW1"),  # PEC
        ("SA1", "VIC1"),
        ("TAS1", "VIC1"),
        ("VIC1", "NSW1"),
        ("VIC1", "SA1"),
        ("VIC1", "TAS1"),
    ),
)
