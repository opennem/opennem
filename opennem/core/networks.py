from datetime import datetime

from opennem.schema.network import NETWORKS, NetworkAPVI, NetworkAU, NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE


def network_from_network_code(network_code: str) -> NetworkSchema:
    network_code = network_code.upper().strip()

    if network_code == "AU":
        return NetworkAU

    if network_code == "WEM":
        return NetworkWEM

    if network_code == "WEMDE":
        return NetworkWEMDE

    if network_code == "NEM":
        return NetworkNEM

    if network_code == "APVI":
        return NetworkAPVI

    network_lookup = list(filter(lambda n: n.code == network_code, NETWORKS))

    if len(network_lookup):
        return network_lookup.pop()

    raise ValueError(f"Unknown network {network_code}")


def datetime_add_network_timezone(dt: datetime, network: NetworkSchema) -> datetime:
    """Returns a datetime in network timezone"""
    return dt.astimezone(network.get_fixed_offset())
