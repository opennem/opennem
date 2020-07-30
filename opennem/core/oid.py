"""
    Module that generated opennem ids

"""

from opennem.core import base24

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


def get_ocode(station) -> str:
    """

        format: {country}_{network}_{region}_{station}_{id}
    """
    values = [
        station.network.country or "au",
        station.network.code or None,
        station.network_region or None,
        station.state or None,
        station.code or None,
        station.id,
    ]

    values = [str(i).lower() for i in values if i is not None]

    ocode = "_".join(values)

    return ocode
