# pylint: disable=no-member
"""
create mv_wem_facility_power_30min

Revision ID: e6bb59b27a23
Revises: 26ecffa41c19
Create Date: 2021-01-22 02:08:14.124716

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e6bb59b27a23"
down_revision = "26ecffa41c19"
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
    where fs.network_id = 'WEM'
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
