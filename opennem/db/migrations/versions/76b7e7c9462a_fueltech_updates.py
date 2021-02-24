# pylint: disable=no-member
"""
Fueltech updates

Revision ID: 76b7e7c9462a
Revises: 2ed53b064d85
Create Date: 2021-02-25 05:54:05.861570

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "76b7e7c9462a"
down_revision = "2ed53b064d85"
branch_labels = None
depends_on = None

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
}


def get_update_sql(code: str, fueltech_id: str) -> str:
    return f"update facility set fueltech_id='{fueltech_id}' where code='{code}'"


def upgrade() -> None:
    for facility_code, fueltech_id in FUELTECHS.items():
        op.execute(get_update_sql(facility_code, fueltech_id))


def downgrade() -> None:
    pass
