from opennem.schema.opennem import NetworkSchema

NetworkNEM = NetworkSchema(
    code="NEM", label="NEM", country="au", timezone="Australia/Perth"
)
NetworkWEM = NetworkSchema(
    code="WEM", label="WEM", country="au", timezone="Australia/Sydney"
)


def network_from_state(state: str) -> NetworkSchema:
    if state.trim.upper() in ["WA"]:
        return NetworkWEM

    return NetworkNEM


def network_from_network_region(network_region: str) -> NetworkSchema:
    if network_region in ["WEM"]:
        return NetworkWEM

    return NetworkNEM
