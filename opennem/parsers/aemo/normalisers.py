""" Data cleaners and normalizers for AEMO source data """
import logging
import re

from opennem.core.normalizers import clean_float

logger = logging.getLogger("opennem.parsers.aemo.schema")


AEMO_GI_FUELTECH_MAP = {
    "Solar": "solar_utility",
    "Battery Storage": "battery_charging",
    "Coal": "coal_black",
    "CCGT": "gas_ccgt",
    "Water": "hydo",
    "Wind": "wind",
    "Biomass": "bioenergy_biomass",
    "OCGT": "gas_ocgt",
}

AEMO_GI_STATUS_MAP = {
    "Anticipated": "announced",
    "Committed": "committed",
    "Publicly Announced Upgrade": "operating",
    "Committed¹": "committed",
    "Committed Upgrade": "operating",
    "Withdrawn - Permanent": None,
    "Committed*": "committed",
    "In Service - Announced Withdrawal (Permanent)": "operating",
    "In Commissioning": "commissioning",
    "In Service": "operating",
    "Publicly Announced": "announced",
    "Anticipated Upgrade": "operating",
}


def aemo_gi_fueltech_to_fueltech(gi_fueltech: str | None) -> str | None:
    """Map AEMO GI fueltech to OpenNEM fueltech"""
    if not gi_fueltech:
        return None

    if gi_fueltech not in AEMO_GI_FUELTECH_MAP.keys():
        return None

    return AEMO_GI_FUELTECH_MAP[gi_fueltech]


def aemo_gi_status_map(gi_status: str | None) -> str | None:
    """Map AEMO GI status to OpenNEM status"""
    if not gi_status:
        return None

    if gi_status not in AEMO_GI_STATUS_MAP.keys():
        return None

    return AEMO_GI_STATUS_MAP[gi_status]


def clean_closure_year_expected(input_year: str | int) -> int | None:
    """ """
    if isinstance(input_year, int):
        return input_year

    return int(input_year.strip()) if input_year and input_year.strip() else None


def aemo_gi_capacity_cleaner(cap: str | None) -> float | None:
    """Custom capacity cleaner because sometimes its parsed as silly
    text like a range (ie. '150 - 180'"""
    if isinstance(cap, int) or isinstance(cap, float):
        return cap

    if not cap:
        return None

    cap = cap.strip()

    num_part = re.search(r"^[\d\.]+", cap)

    if not num_part:
        return None

    num_extracted = str(num_part.group(0))

    num_extracted_and_clean = clean_float(num_extracted)

    return num_extracted_and_clean
