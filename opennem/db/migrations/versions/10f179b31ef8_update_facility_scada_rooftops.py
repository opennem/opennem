# pylint: disable=no-member
"""
update facility scada rooftops

Revision ID: 10f179b31ef8
Revises: 15f5aaf2699c
Create Date: 2020-11-17 18:13:43.209415

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "10f179b31ef8"
down_revision = "15f5aaf2699c"
branch_labels = None
depends_on = None


def upgrade():

    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_TAS' where facility_code = 'ROOFTOP_TAS'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_QLD' where facility_code = 'ROOFTOP_QLD'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_NSW' where facility_code = 'ROOFTOP_NSW'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_VIC' where facility_code = 'ROOFTOP_VIC'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_SA' where facility_code = 'ROOFTOP_SA'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_WA' where facility_code = 'ROOFTOP_WA'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_APVI_NT' where facility_code = 'ROOFTOP_NT'"
    )


def downgrade():

    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_TAS' where facility_code = 'ROOFTOP_APVI_TAS'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_QLD' where facility_code = 'ROOFTOP_APVI_QLD'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_VIC' where facility_code = 'ROOFTOP_APVI_VIC'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_SA' where facility_code = 'ROOFTOP_APVI_SA'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_WA' where facility_code = 'ROOFTOP_APVI_WA'"
    )
    op.execute(
        "update facility_scada set facility_code = 'ROOFTOP_NT' where facility_code = 'ROOFTOP_APVI_NT'"
    )
