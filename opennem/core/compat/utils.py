"""
OpenNEM v2 -> v3 compatability methods

"""

from opennem.schema.network import NetworkNEM

from .fueltechs import map_v2_fueltech, map_v3_fueltech


def translate_id_v3_to_v2(v3_id: str) -> str:
    """Translates v3 ids to v2 ids"""
    idc = id2 = v3_id.split(".")

    if idc[0].lower() == "nem":
        id2 = id2[1:]

    stat_type = idc[-1]

    if stat_type in ["energy", "power", "market_value", "emissions"]:
        fueltech_old = idc[-2]
        fueltech = map_v3_fueltech(fueltech_old)
        id2 = [idc[1], "fuel_tech", fueltech, stat_type]

    if stat_type in ["temperature", "temperature_mean", "temperature_max"]:
        id2 = [idc[1], idc[-1]]

    return ".".join([i for i in id2 if i])


def translate_id_v2_to_v3(v2_id: str) -> str:
    network = NetworkNEM

    idc = v2_id.split(".")

    if idc[0] != network.code:
        idc.insert(0, network.code.lower())

    stat_type = idc[-1]

    if stat_type in ["energy", "power", "market_value", "emissions"]:
        fueltech_old = idc[-2]
        fueltech = map_v2_fueltech(fueltech_old)
        # id2 = [idc[1], "fuel_tech", fueltech, stat_type]
        idc[-2] = fueltech

    return ".".join([i for i in idc if i])


def fix_date_v2(date_str: str) -> str:
    """Fix v2 dates so they're ISO"""
    if date_str.endswith("+1000"):
        date_str = date_str[:-2]

    return date_str
