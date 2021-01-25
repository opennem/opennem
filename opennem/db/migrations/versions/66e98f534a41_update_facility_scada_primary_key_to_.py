# pylint: disable=no-member
"""
update facility_scada primary key to include is_forecast

Revision ID: 66e98f534a41
Revises: 07d27793b5e2
Create Date: 2021-01-25 17:43:00.755467

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "66e98f534a41"
down_revision = "07d27793b5e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL synchronize_seqscans = off;")

    op.execute("ALTER TABLE facility_scada DROP CONSTRAINT facility_scada_pkey CASCADE")

    # ensure is_forecast has values
    op.execute("update facility_scada set is_forecast = False where is_forecast is null")

    op.create_primary_key(
        "facility_scada_pkey",
        "facility_scada",
        ["network_id", "trading_interval", "facility_code", "is_forecast"],
    )


def downgrade() -> None:
    op.execute("SET LOCAL synchronize_seqscans = off;")

    op.execute("ALTER TABLE facility_scada DROP CONSTRAINT facility_scada_pkey CASCADE")
    op.create_primary_key(
        "facility_scada_pkey",
        "facility_scada",
        ["network_id", "trading_interval", "facility_code"],
    )
