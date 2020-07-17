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
    "biogas": "bioenergy_biogas",
    "biomass": "bioenergy_biomass",
    "coal": "coal_black",
    "distillate": "distillate",
    "waste coal mine gas": "gas_wcmg",
    "battery storage": "battery_discharging",
    "landfill methane / landfill": "bioenergy_biomass",
    "municipal solid waste": "bioenergy_biomass",
    "landfill methane / landfill gas": "bioenergy_biogas",
    "bagasse": "bioenergy_biomass",
    "coal seam methane": "bioenergy_biogas",
    "green and air dried wood": "bioenergy_biogas",
    "renewable/ biomass / waste": "bioenergy_biomass",
    "fuel oil": {"turbine - ocgt": "distillate"},
    "kerosene": "distillate",
    "fossil": {
        "open cycle gas turbines (ocgt)": "gas_ocgt",
        "compression reciprocating engine": "gas_wcmg",
        "combined cycle gas turbine (ccgt)": "gas_ccgt",
    },
    "other": {
        "solar pv - fixed": "solar_utility",
        "storage - battery": "battery_discharging",
        "wind turbine - onshore": "wind",
    },
}


def lookup_fueltech(fueltype, techtype=None, fueltype_desc=None):
    ft = fueltype.lower().strip().replace("-", "")
    tt = techtype.lower().strip() if techtype else None
    ftd = fueltype_desc.lower().strip() if fueltype_desc else None

    # Lookup legacy fuel tech types and map them
    if ft in LEGACY_FUELTECH_MAP.keys():
        return LEGACY_FUELTECH_MAP[ft]

    if ftd and ftd in FUELTECH_MAP.keys():
        return FUELTECH_MAP[ftd]

    # Lookup others
    if not ft in FUELTECH_MAP.keys():
        logger.error("Found fueltech {} with no mapping".format(ft))
        return None

    lookup = FUELTECH_MAP[ft]

    if type(lookup) is dict:
        if not tt:
            raise Exception(
                "Require tech type for lookup key {}".format(fueltype)
            )

        if tt in lookup.keys():
            return lookup[tt]

        logger.error(
            "Fueltech lookup failure: No tech type {} for fuel type {}".format(
                techtype, fueltype
            )
        )

        return None

    return lookup
