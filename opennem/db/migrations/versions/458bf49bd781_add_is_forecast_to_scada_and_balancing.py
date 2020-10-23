"""Add is_forecast to scada and balancing

Revision ID: 458bf49bd781
Revises: b16d7153a221
Create Date: 2020-10-24 00:55:23.513798

"""
import sqlalchemy as sa
from alembic import op

revision = "458bf49bd781"
down_revision = "b16d7153a221"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "balancing_summary",
        sa.Column("is_forecast", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "facility_scada", sa.Column("is_forecast", sa.Boolean(), nullable=True)
    )


def downgrade():
    op.drop_column("facility_scada", "is_forecast")
    op.drop_column("balancing_summary", "is_forecast")
