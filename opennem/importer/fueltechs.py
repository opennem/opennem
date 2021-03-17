import logging

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.importer.fueltechs")

# @TODO put this in an CSV
FUELTECHS = {
    "AGLNOW1": "bioenergy_biomass",
    "AGLSITA1": "bioenergy_biomass",
    "APPIN": "gas_recip",
    "AWABAREF": "bioenergy_biomass",
    "BBASEHOS": "distillate",
    "BERWICK": "bioenergy_biomass",
    "BPLANDF1": "bioenergy_biomass",
    "BROADMDW": "bioenergy_biomass",
    "BROOKLYN": "bioenergy_biomass",
    "BWTR1": "bioenergy_biomass",
    "CLAYTON": "bioenergy_biomass",
    "CONDONG1": "bioenergy_biomass",
    "CORIO1": "bioenergy_biomass",
    "EASTCRK": "bioenergy_biomass",
    "EASTCRK2": "bioenergy_biomass",
    "EDLRGNRD": "bioenergy_biomass",
    "GERMCRK": "gas_recip",
    "GLENNCRK": "gas_recip",
    "GRANGEAV": "bioenergy_biomass",
    "GROSV1": "gas_recip",
    "GROSV2": "gas_recip",
    "HALAMRD1": "bioenergy_biomass",
    "HIGHBRY1": "bioenergy_biomass",
    "JACKSGUL": "bioenergy_biomass",
    "KINCUM1": "bioenergy_biomass",
    "LUCAS2S2": "bioenergy_biomass",
    "LUCASHGT": "bioenergy_biomass",
    "MBAHNTH": "gas_recip",
    "MORNW": "bioenergy_biomass",
    "OAKY2": "gas_recip",
    "PEDLER1": "bioenergy_biomass",
    "REMOUNT": "bioenergy_biomass",
    "ROCHEDAL": "bioenergy_biomass",
    "SHEP1": "bioenergy_biomass",
    "STAPYLTON1": "bioenergy_biomass",
    "SVALE1": "bioenergy_biomass",
    "TAHMOOR1": "gas_recip",
    "TATURA01": "bioenergy_biomass",
    "TEATREE1": "bioenergy_biomass",
    "TERALBA": "gas_recip",
    "TITREE": "bioenergy_biomass",
    "TOWER": "gas_recip",
    "WDLNGN01": "bioenergy_biomass",
    "WHIT1": "bioenergy_biomass",
    "WINGF1_1": "bioenergy_biomass",
    "WINGF2_1": "bioenergy_biomass",
    "WOLLERT1": "bioenergy_biomass",
    "WOYWOY1": "bioenergy_biomass",
    "WYNDW": "bioenergy_biomass",
    "LBBL1": "wind",
    "BLAIRFOX_BEROSRD_WF1": "wind",
}


def get_update_sql(code: str, fueltech_id: str) -> str:
    return f"update facility set fueltech_id='{fueltech_id}' where code='{code}'"


def init_fueltechs() -> None:
    engine = get_database_engine()

    with engine.connect() as c:
        for facility_code, fueltech_id in FUELTECHS.items():
            c.execute(get_update_sql(facility_code, fueltech_id))
            logger.debug("Updated fueltech for {}".format(facility_code))

    logger.info("Done updating facility fueltechs")


if __name__ == "__main__":
    init_fueltechs()
