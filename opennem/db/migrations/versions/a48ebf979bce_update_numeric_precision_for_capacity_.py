# pylint: disable=no-member
"""
update_numeric_precision_for_capacity_and_emissions

Revision ID: a48ebf979bce
Revises: 77fcdc3ffe4c
Create Date: 2025-06-23 04:40:40.583851

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'a48ebf979bce'
down_revision = '77fcdc3ffe4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update numeric precision for capacity_registered and emissions_factor_co2.
    Changes precision to (16,4) to limit decimal places to 4.
    """
    # Update units table
    op.alter_column('units', 'capacity_registered',
                    type_=sa.Numeric(precision=16, scale=4),
                    existing_type=sa.Numeric(),
                    existing_nullable=True)

    # Update unit_history table
    op.alter_column('unit_history', 'capacity_registered',
                    type_=sa.Numeric(precision=16, scale=4),
                    existing_type=sa.Numeric(),
                    existing_nullable=True)

    op.alter_column('unit_history', 'emissions_factor_co2',
                    type_=sa.Numeric(precision=16, scale=4),
                    existing_type=sa.Numeric(precision=20, scale=6),
                    existing_nullable=True)

    # Also update emissions_factor_co2 in units table for consistency
    op.alter_column('units', 'emissions_factor_co2',
                    type_=sa.Numeric(precision=16, scale=4),
                    existing_type=sa.Numeric(precision=20, scale=6),
                    existing_nullable=True)


def downgrade() -> None:
    """
    Revert numeric precision changes.
    """
    # Revert units table
    op.alter_column('units', 'capacity_registered',
                    type_=sa.Numeric(),
                    existing_type=sa.Numeric(precision=16, scale=4),
                    existing_nullable=True)

    op.alter_column('units', 'emissions_factor_co2',
                    type_=sa.Numeric(precision=20, scale=6),
                    existing_type=sa.Numeric(precision=16, scale=4),
                    existing_nullable=True)

    # Revert unit_history table
    op.alter_column('unit_history', 'capacity_registered',
                    type_=sa.Numeric(),
                    existing_type=sa.Numeric(precision=16, scale=4),
                    existing_nullable=True)

    op.alter_column('unit_history', 'emissions_factor_co2',
                    type_=sa.Numeric(precision=20, scale=6),
                    existing_type=sa.Numeric(precision=16, scale=4),
                    existing_nullable=True)
