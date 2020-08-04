"""
    Module that generated opennem ids

"""

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


def get_network_region(network_region: str) -> str:
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


def get_ocode(station) -> str:
    """

        format: {country}_{network}_{region}_{station}_{id}
    """
    values = [
        station.network.country or "au",
        station.network.code or None,
        get_network_region(station.facility.network_region),
        station.code or None,
        station.id,
    ]

    values = [str(i).lower() for i in values if i is not None]

    ocode = "_".join(values)

    return ocode
