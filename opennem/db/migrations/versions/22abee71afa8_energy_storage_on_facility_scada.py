# pylint: disable=no-member
"""
energy storage on facility scada

Revision ID: 22abee71afa8
Revises: 4b97fb58f802
Create Date: 2025-09-03 10:11:30.352413

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '22abee71afa8'
down_revision = '4b97fb58f802'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('facility_scada', sa.Column('energy_storage', sa.Numeric(precision=20, scale=6), nullable=True))


def downgrade() -> None:
    op.drop_column('facility_scada', 'energy_storage')
