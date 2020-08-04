"""
    Module that generated opennem ids

"""

from typing import Optional

from opennem.core import base24
from opennem.core.normalizers import is_number

# from opennem.db.models.opennem import Station


def get_oid(model) -> str:
    _id = model.id

    if not model.id:
        return None

    parent_oid = None

    if hasattr(model, "station"):
        parent_oid = get_oid(model.station)

    item_oid = base24.dumps(_id)

    oid_components = [
        parent_oid,
        item_oid,
    ]

    oid_string = "_".join([str(i) for i in oid_components if i])

    return oid_string


def get_network_region(network_region: str) -> Optional[str]:
    """
        Trim the numbers off the end of nem regions

    """
    if (
        network_region
        and type(network_region) is str
        and len(network_region) > 1
    ):
        if is_number(network_region[-1:]):
            return network_region[:-1]
        return network_region

    return None


def get_station_facility(station):
    """
        Get the first facility for a station

    """
    if (station.facilities) and len(station.facilities) > 0:
        return station.facilities[0]

    return None


def get_ocode(station) -> str:
    """

        format: {country}_{network}_{region}_{station}_{id}
    """
    facility = get_station_facility(station)

    values = [
        station.network.country or "au",
        station.network.code or None,
        get_network_region(facility.network_region) or station.state,
        station.code or None,
        station.id,
    ]

    values = [str(i).lower() for i in values if i is not None]

    ocode = "_".join(values)

    return ocode
