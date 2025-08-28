# pylint: disable=no-member
"""
Update stats value column precision to 1 decimal place

Revision ID: 4b97fb58f802
Revises: 27431059b549
Create Date: 2025-08-28 03:00:45.275604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b97fb58f802'
down_revision = '27431059b549'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change stats.value column to Numeric(10, 4) for proper CPI precision"""
    # Update the column type to have proper precision
    op.alter_column('stats', 'value',
               existing_type=sa.Numeric(),
               type_=sa.Numeric(precision=10, scale=4),
               existing_nullable=True)

    # Round existing values to 4 decimal places
    op.execute("UPDATE stats SET value = ROUND(value::numeric, 4) WHERE stat_type = 'CPI'")


def downgrade() -> None:
    """Revert stats.value column back to plain Numeric"""
    op.alter_column('stats', 'value',
               existing_type=sa.Numeric(precision=10, scale=4),
               type_=sa.Numeric(),
               existing_nullable=True)
