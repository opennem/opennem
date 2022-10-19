import csv
import logging
from pkgutil import get_data
from typing import Dict, List, Optional

from opennem.core.dispatch_type import DispatchType
from opennem.core.loader import load_data
from opennem.schema.fueltech import FueltechSchema

logger = logging.getLogger(__name__)


class FueltechException(Exception):
    pass


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
    if type(ft) is not str:
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
    csv_data = get_data("opennem", f"core/data/{fixture_name}")

    if not csv_data:
        raise FueltechException(f"Could not load fixture: {fixture_name}")

    csv_data = csv_data.decode("utf-8-sig").splitlines()

    fueltech_map = {}

    csvreader = csv.DictReader(csv_data)

    for line in csvreader:
        record = [i or None for field, i in line.items() if field in MAP_KEYS]

        records = list(map(clean_fueltech, record))

        key = tuple(records)

        fueltech_map[key] = line["fueltech_map"]

    return fueltech_map


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

    fueltech_map = load_fueltech_map("aemo_fueltech_map.csv")

    ft = clean_fueltech(fueltype)

    if techtype:
        tt = clean_fueltech(techtype)

    if fueltype_desc:
        ftd = clean_fueltech(fueltype_desc)

    if techtype_desc:
        ttd = clean_fueltech(techtype_desc)

    # @NOTE don't touch this line - it creates a tuple that is used as the lookup
    # key. should match what is in the generated map
    lookup_set = ft, ftd, tt, ttd, dispatch_type.value.lower()

    # Lookup legacy fuel tech types and map them
    if ft and ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if lookup_set in fueltech_map:
        return fueltech_map[lookup_set]

    logger.warning(f"Found fueltech {ft}, {tt}, {ftd}, {ttd} with no mapping")

    return None


def map_v2_fueltech(
    fueltech: str,
) -> str:
    """
    Takes a v2 fueltech and maps it to v3

    """

    ft = clean_fueltech(fueltech)

    # Lookup legacy fuel tech types and map them
    return LEGACY_FUELTECH_MAP[ft] if ft in LEGACY_FUELTECH_MAP.keys() else ft


def map_v3_fueltech(
    fueltech: str,
) -> str:
    """
    Takes a v3 fueltech and maps it to v2

    """

    ft = clean_fueltech(fueltech)

    return next(
        (v2_fueltech for v2_fueltech, v3_fueltech in LEGACY_FUELTECH_MAP.items() if v3_fueltech == fueltech), ft
    )


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

    if _lookup := list(filter(lambda x: x.code == _code, _FUELTECHS)):
        return _lookup.pop()
    else:
        raise FueltechException(f"Fueltech {_code} not found")
