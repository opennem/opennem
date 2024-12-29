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
