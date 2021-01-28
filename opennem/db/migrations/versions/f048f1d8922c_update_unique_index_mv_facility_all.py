# pylint: disable=no-member
"""
Update unique index mv_facility_all

Revision ID: f048f1d8922c
Revises: 53521de3619b
Create Date: 2021-01-28 18:24:47.305094

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f048f1d8922c"
down_revision = "53521de3619b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_facility_unique ON mv_facility_all (trading_interval, network_id, code);"
    )


def downgrade() -> None:
    op.execute("drop index idx_mv_facility_unique;")
