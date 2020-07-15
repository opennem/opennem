import logging

logger = logging.getLogger(__name__)

LEGACY_FUELTECH_MAP = {
    "brown_coal": "coal_brown",
    "black_coal": "coal_black",
    "solar": "solar_utility",
    "biomass": "bioenergy_biomass",
}


FUELTECH_MAP = {
    "wind": "wind",
    "solar": "solar_utility",
    "gas": "gas_ccgt",
    "landfill gas": "bioenergy_biogas",
    "biomass": "bioenergy_biomass",
    "distillate": "distillate",
    "black coal": "coal_black",
    "brown coal": "coal_brown",
    "water": "hydro",
    "diesel": "distillate",
    "wind": "wind",
    "solar": "solar_utility",
    "gas": "gas_ccgt",
    "landfill gas": "bioenergy_biogas",
    "biomass": "bioenergy_biomass",
    "coal": "coal_black",
    "distillate": "distillate",
    "waste coal mine gas": "gas_wcmg",
    "landfill methane / landfill": "bioenergy_biomass",
    "landfill methane / landfill gas": "bioenergy_biogas",
    "bagasse": "bioenergy_biomass",
    "coal seam methane": "bioenergy_biogas",
}


FUELTECH_MAP_FROM_TECHS = {
    "solar pv - fixed": "solar",
    # "Reciprocating Engine - Compression ignition": "",
    # "Reciprocating Engine - Spark ignition": "",
    "storage - battery": "battery_discharging",
    # "Storage - Virtual Power Plant": "",
    # "Turbine - Steam Sub Critical": "",
    "wind turbine - onshore": "wind",
}


def lookup_fueltech(fueltype, techtype=None):
    ft = fueltype.lower()
    tt = techtype.lower()

    if ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if ft == "other":
        if not techtype:
            logger.error(
                "Missing mapping for other fueltech with techtype: {}".format(
                    techtype
                )
            )
            return None

        if not tt in FUELTECH_MAP_FROM_TECHS.keys():
            logger.error(
                "Found fueltech other with tech type {}  that doesn't map "
            )
            return None

    if not ft in FUELTECH_MAP.keys():
        logger.error("Found fueltech {} with no mapping".format(ft))
        return None

    return FUELTECH_MAP[ft]
