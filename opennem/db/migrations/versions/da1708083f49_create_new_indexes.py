# pylint: disable=no-member
"""
create new indexes

Revision ID: da1708083f49
Revises: 0c22c0ca02e8
Create Date: 2024-08-11 12:04:28.979319

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "da1708083f49"
down_revision = "0c22c0ca02e8"
branch_labels = None
depends_on = None


def upgrade():
    # On facility_scada
    op.create_index('idx_facility_scada_is_forecast_interval', 'facility_scada', ['is_forecast', 'interval'])
    op.create_index('idx_facility_scada_network_interval', 'facility_scada', ['network_id', 'interval', 'is_forecast'])

    # On facility
    op.create_index('idx_facility_fueltech_id', 'facility', ['fueltech_id'])

    # On fueltech
    op.create_index('idx_fueltech_code', 'fueltech', ['code'])

    # On network
    op.create_index('idx_network_code', 'network', ['code'])

def downgrade():
    # On network
    op.drop_index('idx_network_code', table_name='network')

    # On fueltech
    op.drop_index('idx_fueltech_code', table_name='fueltech')

    # On facility
    op.drop_index('idx_facility_fueltech_id', table_name='facility')

    # On facility_scada
    op.drop_index('idx_facility_scada_network_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_is_forecast_interval', table_name='facility_scada')
