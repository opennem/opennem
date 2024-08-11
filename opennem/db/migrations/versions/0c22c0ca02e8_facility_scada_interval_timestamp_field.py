# pylint: disable=no-member
"""
facility_scada interval timestamp field

Revision ID: 0c22c0ca02e8
Revises: 9206f088ad6a
Create Date: 2024-08-11 11:30:21.019596

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "0c22c0ca02e8"
down_revision = "9206f088ad6a"
branch_labels = None
depends_on = None



def upgrade():
    # Add new column
    op.add_column('facility_scada', sa.Column('interval', sa.TIMESTAMP(timezone=False)))

    # Update the new column
    op.execute(text("""
        UPDATE facility_scada fs
        SET interval = fs.trading_interval AT TIME ZONE n.timezone
        FROM network n
        WHERE fs.network_id = n.code
    """))

    # Create new table
    op.create_table(
        'facility_scada_new',
        sa.Column('network_id', sa.Text(), nullable=False),
        sa.Column('interval', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('facility_code', sa.Text(), nullable=False),
        sa.Column('generated', sa.Numeric()),
        sa.Column('eoi_quantity', sa.Numeric()),
        sa.Column('is_forecast', sa.Boolean(), nullable=False),
        sa.Column('energy_quality_flag', sa.Numeric(), nullable=False),
        sa.PrimaryKeyConstraint('network_id', 'interval', 'facility_code', 'is_forecast', name='facility_scada_new_pkey')
    )

    # Create hypertable (Note: This is TimescaleDB specific and might need adjustment)
    op.execute(text("SELECT create_hypertable('facility_scada_new', 'interval', chunk_time_interval => INTERVAL '7 days')"))

    # Copy data
    op.execute(text("""
        INSERT INTO facility_scada_new (
            network_id,
            interval,
            facility_code,
            generated,
            eoi_quantity,
            is_forecast,
            energy_quality_flag
        )
        SELECT
            network_id,
            interval,
            facility_code,
            generated,
            eoi_quantity,
            is_forecast,
            energy_quality_flag
        FROM facility_scada
        ON CONFLICT (network_id, interval, facility_code, is_forecast) DO NOTHING
    """))

    # Create indexes
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada_new', ['facility_code', 'interval'], unique=False)
    op.create_index('idx_facility_scada_network_id', 'facility_scada_new', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_interval_facility_code', 'facility_scada_new', ['interval', 'facility_code'], unique=False)

    # Drop old table
    op.drop_table('facility_scada')

    # Rename new table
    op.rename_table('facility_scada_new', 'facility_scada')

def downgrade():
    # Note: This downgrade function is a basic reversal and might not perfectly restore the original state
    op.rename_table('facility_scada', 'facility_scada_new')

    op.create_table(
        'facility_scada',
        sa.Column('network_id', sa.Text(), nullable=False),
        sa.Column('trading_interval', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('facility_code', sa.Text(), nullable=False),
        sa.Column('generated', sa.Numeric()),
        sa.Column('eoi_quantity', sa.Numeric()),
        sa.Column('is_forecast', sa.Boolean(), nullable=False),
        sa.Column('energy_quality_flag', sa.Numeric(), nullable=False),
        sa.PrimaryKeyConstraint('network_id', 'trading_interval', 'facility_code', 'is_forecast')
    )

    op.execute(text("""
        INSERT INTO facility_scada
        SELECT
            network_id,
            interval AT TIME ZONE n.timezone as trading_interval,
            facility_code,
            generated,
            eoi_quantity,
            is_forecast,
            energy_quality_flag
        FROM facility_scada_new fs
        JOIN network n ON fs.network_id = n.code
        ON CONFLICT (network_id, trading_interval, facility_code, is_forecast) DO NOTHING
    """))

    op.create_index('idx_facility_scada_facility_code_trading_interval', 'facility_scada', ['facility_code', 'trading_interval'], unique=False)
    op.create_index('idx_facility_scada_network_id', 'facility_scada', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_trading_interval_facility_code', 'facility_scada', ['trading_interval', 'facility_code'], unique=False)

    op.drop_table('facility_scada_new')
