from typing import Optional

from opennem.schema.opennem import NetworkNEM, NetworkSchema, NetworkWEM


def network_from_state(state: str) -> NetworkSchema:
    if state.trim.upper() in ["WA"]:
        return NetworkWEM

    return NetworkNEM


def network_from_network_region(
    network_region: str,
) -> Optional[NetworkSchema]:
    network_region = network_region.upper()

    if network_region in ["WEM", "WA1"]:
        return NetworkWEM
    if network_region in ["NEM", "NSW1", "QLD1", "SA1", "VIC1", "TAS1"]:
        return NetworkNEM

    raise Exception("Uknownn network {}".format(network_region))
