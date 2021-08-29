import csv
import logging
from pkgutil import get_data
from typing import Dict, List, Optional

from opennem.core.dispatch_type import DispatchType, dispatch_type_string, parse_dispatch_type
from opennem.core.loader import load_data
from opennem.schema.fueltech import FueltechSchema

logger = logging.getLogger(__name__)

LEGACY_FUELTECH_MAP = {
    "brown_coal": "coal_brown",
    "black_coal": "coal_black",
    "solar": "solar_utility",
    "rooftop_solar": "solar_rooftop",
    "biomass": "bioenergy_biomass",
}


def clean_fueltech(ft: str) -> Optional[str]:
    """
    Clean the fueltech strings that come out of the spreadsheets
    or other sources

    @TODO replace with a compiled regexp
    """
    if not type(ft) is str:
        return None

    if ft == "-":
        return None

    ft = ft.lower().strip()

    if ft == "":
        return None

    return ft


def load_fueltech_map(fixture_name: str) -> Dict:
    """
    Reads the CSV to load the fueltech map

    Fields are:

    fuel_source,fuel_source_desc,tech,tech_desc,fueltech_map,load_type

    """

    MAP_KEYS = [
        "fuel_source",
        "fuel_source_desc",
        "tech",
        "tech_desc",
        "load_type",
    ]

    # Funky encoding because of save from Excel .. leave it
    csv_data = get_data("opennem", "core/data/{}".format(fixture_name))

    if not csv_data:
        raise Exception("Could not load fixture: {}".format(fixture_name))

    csv_data = csv_data.decode("utf-8-sig").splitlines()

    fueltech_map = {}

    csvreader = csv.DictReader(csv_data)

    for line in csvreader:
        record = [i or None for field, i in line.items() if field in MAP_KEYS]

        records = list(map(clean_fueltech, record))

        # records[4] = parse_dispatch_type(records[4])

        key = tuple(records)

        fueltech_map[key] = line["fueltech_map"]

    return fueltech_map


FUELTECH_MAP = load_fueltech_map("aemo_fueltech_map.csv")


def lookup_fueltech(
    fueltype: str,
    fueltype_desc: Optional[str] = None,
    techtype: Optional[str] = None,
    techtype_desc: Optional[str] = None,
    dispatch_type: DispatchType = DispatchType.GENERATOR,
) -> Optional[str]:
    """
    Takes fueltech strings from AEMO or other sources and maps them
    to opennem fueltechs using the csv file in the data directory

    """
    tt, ftd, ttd = None, None, None

    ft = clean_fueltech(fueltype)

    if techtype:
        tt = clean_fueltech(techtype)

    if fueltype_desc:
        ftd = clean_fueltech(fueltype_desc)

    if techtype_desc:
        ttd = clean_fueltech(techtype_desc)

    lookup_set = tuple([ft, ftd, tt, ttd, dispatch_type.value.lower()])

    # Lookup legacy fuel tech types and map them
    if ft and ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if lookup_set in FUELTECH_MAP:
        return FUELTECH_MAP[lookup_set]

    logger.warning("Found fueltech {}, {}, {}, {} with no mapping".format(ft, tt, ftd, ttd))

    return None


def map_v2_fueltech(
    fueltech: str,
) -> str:
    """
    Takes a v2 fueltech and maps it to v3

    """

    ft = clean_fueltech(fueltech)

    # Lookup legacy fuel tech types and map them
    if ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    return ft


def map_v3_fueltech(
    fueltech: str,
) -> str:
    """
    Takes a v3 fueltech and maps it to v2

    """

    ft = clean_fueltech(fueltech)

    # Lookup legacy fuel tech types and map them
    for v2_fueltech, v3_fueltech in LEGACY_FUELTECH_MAP.items():
        if v3_fueltech == fueltech:
            return v2_fueltech

    return ft


def get_fueltechs() -> List[FueltechSchema]:
    fixture = load_data("fueltechs.json", from_fixture=True)

    fueltechs = []
    f: Dict = None

    for f in fixture:
        _f = FueltechSchema(**f)
        fueltechs.append(_f)

    return fueltechs


_FUELTECHS: List[FueltechSchema] = get_fueltechs()


def get_fueltech(code: str) -> FueltechSchema:
    _code = code.strip().lower()

    _lookup = list(filter(lambda x: x.code == _code, _FUELTECHS))

    if not _lookup:
        raise Exception(f"Fueltech {_code} not found")

    return _lookup.pop()
