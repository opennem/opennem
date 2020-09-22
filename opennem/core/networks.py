from opennem.schema.opennem import NetworkNEM, NetworkSchema, NetworkWEM


def network_from_state(state: str) -> NetworkSchema:
    if state.trim.upper() in ["WA"]:
        return NetworkWEM

    return NetworkNEM


def network_from_network_region(network_region: str) -> NetworkSchema:
    if network_region in ["WEM"]:
        return NetworkWEM

    return NetworkNEM
