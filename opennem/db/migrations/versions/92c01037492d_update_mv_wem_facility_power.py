# pylint: disable=no-member
"""
Update mv_wem_facility_power

Revision ID: 92c01037492d
Revises: e6bb59b27a23
Create Date: 2021-01-22 14:39:27.577816

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "92c01037492d"
down_revision = "e6bb59b27a23"
branch_labels = None
depends_on = None


stmt_drop = "drop materialized view if exists mv_wem_facility_power_30min cascade;"

stmt = """
CREATE MATERIALIZED VIEW mv_wem_facility_power_30min WITH (timescaledb.continuous) AS
select
    time_bucket('30 minutes', fs.trading_interval) as trading_interval,
    fs.facility_code,
    max(fs.generated) as facility_power
from facility_scada fs
where fs.network_id in ('WEM', 'APVI')
group by
    1,
    fs.facility_code;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
