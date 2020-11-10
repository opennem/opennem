from opennem.schema.network import (
    NetworkAU,
    NetworkNEM,
    NetworkSchema,
    NetworkWEM,
)


def network_from_state(state: str) -> NetworkSchema:
    state = state.upper().strip()

    if state in ["WA"]:
        return NetworkWEM

    if state in ["QLD", "NSW", "VIC", "ACT", "TAS", "SA", "NT"]:
        return NetworkNEM

    raise Exception("Unknown network {}".format(state))


def network_from_network_region(network_region: str,) -> NetworkSchema:
    network_region = network_region.upper()

    if network_region in ["WEM", "WA1"]:
        return NetworkWEM
    if network_region in ["NEM", "NSW1", "QLD1", "SA1", "VIC1", "TAS1"]:
        return NetworkNEM

    raise Exception("Unknown network {}".format(network_region))


def network_from_network_code(network_code: str) -> NetworkSchema:
    network_code = network_code.upper().strip()

    if network_code in ["AU"]:
        return NetworkAU

    if network_code in ["WEM"]:
        return NetworkWEM

    if network_code in ["NEM"]:
        return NetworkNEM

    raise Exception("Unknown network {}".format(network_code))
