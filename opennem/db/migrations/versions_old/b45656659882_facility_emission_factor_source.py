# pylint: disable=no-member
"""
facility emission factor source

Revision ID: b45656659882
Revises: bcf0dc6c0cc8
Create Date: 2023-01-17 10:50:27.754261

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b45656659882"
down_revision = "bcf0dc6c0cc8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility",
        sa.Column("emission_factor_source", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("facility", "emission_factor_source")
