"""
OpenNEM v2 -> v3 compatability methods

"""

from .fueltechs import map_v3_fueltech


def translate_id_v3_to_v2(v3_id: str) -> str:
    """Translates v3 ids to v2 ids"""
    idc = id2 = v3_id.split(".")

    if idc[0].lower() == "nem":
        id2 = id2[1:]

    stat_type = idc[-1]

    if stat_type in ["energy", "power"]:
        fueltech_old = idc[-2]
        fueltech = map_v3_fueltech(fueltech_old)
        id2 = [idc[1], "fuel_tech", fueltech, stat_type]

    if stat_type in ["temperature"]:
        id2 = [idc[1], idc[-1]]

    return ".".join([i for i in id2 if i])
