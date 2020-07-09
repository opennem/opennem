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
    if not type(ft) is str:
        return None

    if ft == "-":
        return None

    ft = ft.lower().strip()

    if ft == "":
        return None

    return ft


def load_fueltech_map(fixture_name):
    fixture_path = os.path.join(DATA_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fueltech_map = {}

    with open(fixture_path) as fh:
        csvreader = csv.reader(fh)
        for line in csvreader:
            if line[2] == "tech":
                continue

            if len(line) < 4:
                line[3] = None

            key = tuple(map(clean_fueltech, line[:4]))

            val = line[4]

            fueltech_map[key] = val

    return fueltech_map


FUELTECH_MAP = load_fueltech_map("aemo_fueltech_map.csv")


def lookup_fueltech(
    fueltype, fueltype_desc=None, techtype=None, techtype_desc=None
):
    ft = clean_fueltech(fueltype)
    tt = clean_fueltech(techtype)
    ftd = clean_fueltech(fueltype_desc)
    ttd = clean_fueltech(techtype_desc)

    lookup_set = tuple([ft, ftd, tt, ttd])

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
