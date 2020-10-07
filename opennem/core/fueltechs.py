import csv
import logging
from pkgutil import get_data

logger = logging.getLogger(__name__)

LEGACY_FUELTECH_MAP = {
    "brown_coal": "coal_brown",
    "black_coal": "coal_black",
    "solar": "solar_utility",
    "biomass": "bioenergy_biomass",
}


def clean_fueltech(ft):
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


def load_fueltech_map(fixture_name):
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
    csv_data = (
        get_data("opennem", "core/data/{}".format(fixture_name))
        .decode("utf-8-sig")
        .splitlines()
    )

    fueltech_map = {}

    csvreader = csv.DictReader(csv_data)
    for line in csvreader:
        record = [i or None for field, i in line.items() if field in MAP_KEYS]

        key = tuple(map(clean_fueltech, record))

        fueltech_map[key] = line["fueltech_map"]

    return fueltech_map


FUELTECH_MAP = load_fueltech_map("aemo_fueltech_map.csv")


def lookup_fueltech(
    fueltype: str,
    fueltype_desc=None,
    techtype=None,
    techtype_desc=None,
    dispatch_type: str = "generator",
):
    """
        Takes fueltech strings from AEMO or other sources and maps them
        to opennem fueltechs using the csv file in the data directory

    """

    ft = clean_fueltech(fueltype)
    tt = clean_fueltech(techtype)
    ftd = clean_fueltech(fueltype_desc)
    ttd = clean_fueltech(techtype_desc)
    dispatch_type = dispatch_type.strip().lower()

    if dispatch_type not in ["generator", "load"]:
        raise Exception("Invalid dispatch type: {}".format(dispatch_type))

    lookup_set = tuple([ft, ftd, tt, ttd, dispatch_type])

    # Lookup legacy fuel tech types and map them
    if ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if lookup_set in FUELTECH_MAP:
        return FUELTECH_MAP[lookup_set]

    logger.warning(
        "Found fueltech {}, {}, {}, {} with no mapping".format(
            ft, tt, ftd, ttd
        )
    )

    return None
