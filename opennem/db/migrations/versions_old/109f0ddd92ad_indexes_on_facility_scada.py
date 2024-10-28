# pylint: disable=no-member
"""
Indexes on facility_scada

Revision ID: 109f0ddd92ad
Revises: df1a9890f5c8
Create Date: 2021-11-24 09:35:08.922469

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "109f0ddd92ad"
down_revision = "df1a9890f5c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        create index if not exists idx_facility_scada_day_network_fueltech_aest
        on facility_scada (date_trunc('day', trading_interval at time zone 'AEST'), network_id, facility_code)
    """
    )

    op.execute(
        """
        create index if not exists idx_facility_scada_day_network_fueltech_awst
        on facility_scada (date_trunc('day', trading_interval at time zone 'AWST'), network_id, facility_code)
    """
    )


def downgrade() -> None:
    pass
