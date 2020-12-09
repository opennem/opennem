# pylint: disable=no-member
"""Optimized energy_sum sql function

Revision ID: 10f1d9517df7
Revises: 458bf49bd781
Create Date: 2020-10-29 03:25:01.093194

"""
from alembic import op

from opennem.core.loader import load_data

# revision identifiers, used by Alembic.
revision = "10f1d9517df7"
down_revision = "458bf49bd781"
branch_labels = None
depends_on = None


def upgrade():
    ENERGY_FUNCTIONS = load_data(
        "energy_sum_v2.sql", from_fixture=True, content_type="utf-8"
    ).decode("utf-8")
    op.execute(ENERGY_FUNCTIONS)


def downgrade():
    pass
