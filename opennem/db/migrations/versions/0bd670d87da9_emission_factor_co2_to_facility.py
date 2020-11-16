# pylint: disable=no-member
"""Emission factor co2 to facility

Revision ID: 0bd670d87da9
Revises: 69449fda6381
Create Date: 2020-11-13 02:48:57.159985

"""
import sqlalchemy as sa
from alembic import op

revision = "0bd670d87da9"
down_revision = "69449fda6381"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "facility",
        sa.Column("emissions_factor_co2", sa.Numeric(), nullable=True),
    )


def downgrade():
    op.drop_column("facility", "emissions_factor_co2")
