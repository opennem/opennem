# pylint: disable=no-member
"""
energy_quality_flag field type

Revision ID: 06f2e270e664
Revises: 67cc493a27d4
Create Date: 2024-12-29 09:52:11.928212

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '06f2e270e664'
down_revision = '67cc493a27d4'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.alter_column('facility_scada', 'energy_quality_flag',
               existing_type=sa.NUMERIC(),
               type_=sa.SmallInteger(),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('facility_scada', 'energy_quality_flag',
               existing_type=sa.SmallInteger(),
               type_=sa.NUMERIC(),
               existing_nullable=False)
