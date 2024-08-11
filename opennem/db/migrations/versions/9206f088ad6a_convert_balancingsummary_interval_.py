# pylint: disable=no-member
"""
convert BalancingSummary interval without time zone

Revision ID: 9206f088ad6a
Revises: c490cd5e58a2
Create Date: 2024-08-10 14:39:41.976182

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9206f088ad6a"
down_revision = "c490cd5e58a2"
branch_labels = None
depends_on = None

def upgrade():
    # Add new column
    op.add_column('balancing_summary', sa.Column('interval', sa.TIMESTAMP(timezone=False)))

    # Update the new column
    op.execute(text("""
        UPDATE balancing_summary bs
        SET interval = bs.trading_interval AT TIME ZONE n.timezone
        FROM network n
        WHERE bs.network_id = n.code
    """))

    # Create new table
    op.create_table(
        'balancing_summary_new',
        sa.Column('interval', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('network_id', sa.Text(), nullable=False),
        sa.Column('network_region', sa.Text(), nullable=False),
        sa.Column('forecast_load', sa.Numeric()),
        sa.Column('generation_scheduled', sa.Numeric()),
        sa.Column('generation_non_scheduled', sa.Numeric()),
        sa.Column('generation_total', sa.Numeric()),
        sa.Column('price', sa.Numeric()),
        sa.Column('is_forecast', sa.Boolean()),
        sa.Column('net_interchange', sa.Numeric()),
        sa.Column('demand_total', sa.Numeric()),
        sa.Column('price_dispatch', sa.Numeric()),
        sa.Column('net_interchange_trading', sa.Numeric()),
        sa.Column('demand', sa.Numeric()),
        sa.PrimaryKeyConstraint('interval', 'network_id', 'network_region', name='pk_balancing_summary_pkey')
    )

    # Create hypertable (Note: This is TimescaleDB specific and might need adjustment)
    op.execute(text("SELECT create_hypertable('balancing_summary_new', 'interval', chunk_time_interval => INTERVAL '7 days')"))

    # Copy data
    op.execute(text("""
        INSERT INTO balancing_summary_new
        SELECT interval, network_id, network_region, forecast_load, generation_scheduled, generation_non_scheduled,
               generation_total, price, is_forecast, net_interchange, demand_total,
               price_dispatch, net_interchange_trading, demand
        FROM balancing_summary
    """))

    # Drop old table
    op.drop_table('balancing_summary')

    # Rename new table
    op.rename_table('balancing_summary_new', 'balancing_summary')

    # Create indexes
    op.create_index('ix_balancing_summary_interval', 'balancing_summary', ['interval'])
    op.create_index('idx_balancing_summary_network_id_interval', 'balancing_summary', ['network_id', 'interval'], unique=False)
    op.create_index('idx_balancing_summary_network_region_interval', 'balancing_summary', ['network_region', 'interval'], unique=False)

def downgrade():
    # Note: This downgrade function is a basic reversal and might not perfectly restore the original state
    op.drop_index('idx_balancing_summary_network_region_interval', table_name='balancing_summary')
    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary')
    op.drop_index('ix_balancing_summary_interval', table_name='balancing_summary')

    op.rename_table('balancing_summary', 'balancing_summary_new')

    op.create_table(
        'balancing_summary',
        sa.Column('trading_interval', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('network_id', sa.Text(), nullable=False),
        sa.Column('network_region', sa.Text(), nullable=False),
        sa.Column('forecast_load', sa.Numeric()),
        sa.Column('generation_scheduled', sa.Numeric()),
        sa.Column('generation_non_scheduled', sa.Numeric()),
        sa.Column('generation_total', sa.Numeric()),
        sa.Column('price', sa.Numeric()),
        sa.Column('is_forecast', sa.Boolean()),
        sa.Column('net_interchange', sa.Numeric()),
        sa.Column('demand_total', sa.Numeric()),
        sa.Column('price_dispatch', sa.Numeric()),
        sa.Column('net_interchange_trading', sa.Numeric()),
        sa.Column('demand', sa.Numeric()),
        sa.PrimaryKeyConstraint('trading_interval', 'network_id', 'network_region')
    )

    op.execute(text("""
        INSERT INTO balancing_summary
        SELECT interval AT TIME ZONE n.timezone as trading_interval,
               bs.network_id, bs.network_region, forecast_load, generation_scheduled,
               generation_non_scheduled, generation_total, price, is_forecast,
               net_interchange, demand_total, price_dispatch, net_interchange_trading, demand
        FROM balancing_summary_new bs
        JOIN network n ON bs.network_id = n.code
    """))

    op.drop_table('balancing_summary_new')
