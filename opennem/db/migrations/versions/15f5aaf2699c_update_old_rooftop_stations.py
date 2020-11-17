# pylint: disable=no-member
"""
Update old rooftop stations

Revision ID: 15f5aaf2699c
Revises: 0716d393ff9d
Create Date: 2020-11-17 15:05:40.037459

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "15f5aaf2699c"
down_revision = "0716d393ff9d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_TAS' where code = 'ROOFTOP_TAS'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_QLD' where code = 'ROOFTOP_QLD'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_NSW' where code = 'ROOFTOP_NSW'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_VIC' where code = 'ROOFTOP_VIC'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_SA' where code = 'ROOFTOP_SA'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_WA' where code = 'ROOFTOP_WA'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_APVI_NT' where code = 'ROOFTOP_NT'"
    )


def downgrade():
    op.execute(
        "update facility set code = 'ROOFTOP_TAS' where code = 'ROOFTOP_APVI_TAS'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_QLD' where code = 'ROOFTOP_APVI_QLD'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_VIC' where code = 'ROOFTOP_APVI_VIC'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_SA' where code = 'ROOFTOP_APVI_SA'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_WA' where code = 'ROOFTOP_APVI_WA'"
    )
    op.execute(
        "update facility set code = 'ROOFTOP_NT' where code = 'ROOFTOP_APVI_NT'"
    )
