import csv
import logging
import os

logger = logging.getLogger(__name__)

LEGACY_FUELTECH_MAP = {
    "brown_coal": "coal_brown",
    "black_coal": "coal_black",
    "solar": "solar_utility",
    "biomass": "bioenergy_biomass",
}


DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


def clean_fueltech(ft):
    ft = str(ft)

    ft = ft.lower().strip().replace("-", "").replace("  ", " ")

    if ft == "":
        return None

    return ft


def load_facility_stations(fixture_name):
    fixture_path = os.path.join(DATA_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fueltech_map = {}

    with open(fixture_path) as fh:
        csvreader = csv.reader(fh)
        for line in csvreader:
            key = frozenset(map(clean_fueltech, line[:4]))
            val = line[5]

            fueltech_map[key] = val

    return fueltech_map


FUELTECH_MAP = load_facility_stations("aemo_fueltech_map.csv")


def lookup_fueltech(
    fueltype, techtype=None, fueltype_desc=None, techtype_desc=None
):
    ft = clean_fueltech(fueltype)
    tt = clean_fueltech(techtype)
    ftd = clean_fueltech(fueltype_desc)
    ttd = clean_fueltech(techtype_desc)

    lookup_set = frozenset([ft, ftd, tt, ftd])

    # Lookup legacy fuel tech types and map them
    if ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if lookup_set in FUELTECH_MAP:
        return FUELTECH_MAP[lookup_set]

    logger.warn(
        "Found fueltech {}, {}, {}, {} with no mapping".format(
            ft, tt, ftd, ttd
        )
    )

    return None
