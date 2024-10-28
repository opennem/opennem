# pylint: disable=no-member
"""
Facility expected closure date field

Revision ID: edd45c2d6508
Revises: c12510c75208
Create Date: 2021-05-24 17:07:49.030366

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "edd45c2d6508"
down_revision = "c12510c75208"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility",
        sa.Column("expected_closure_date", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("facility", "expected_closure_date")
