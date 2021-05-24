# pylint: disable=no-member
"""
Facility expected closure year field

Revision ID: 0e87606a7f36
Revises: edd45c2d6508
Create Date: 2021-05-24 18:03:27.926912

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0e87606a7f36"
down_revision = "edd45c2d6508"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility",
        sa.Column("expected_closure_year", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("facility", "expected_closure_year")
