"""Create hypertables

Revision ID: ad3938cfbd45
Revises: 28a206c84987
Create Date: 2020-10-16 22:28:23.901036

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ad3938cfbd45"
down_revision = "28a206c84987"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "select create_hypertable('facility_scada', 'trading_interval', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 week')"
    )
    op.execute(
        "select create_hypertable('balancing_summary', 'trading_interval', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 week')"
    )


def downgrade():
    pass
