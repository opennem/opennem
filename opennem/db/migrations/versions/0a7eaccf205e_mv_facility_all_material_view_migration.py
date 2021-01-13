# pylint: disable=no-member
"""
mv_facility_all material view migration

@NOTE this was nullified to speed up deploys
as the next migration recreates with updates

Revision ID: 0a7eaccf205e
Revises: 43f1d539490f
Create Date: 2021-01-12 18:53:42.852651

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0a7eaccf205e"
down_revision = "43f1d539490f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        drop materialized view if exists mv_facility_all;
    """
    )


def downgrade() -> None:
    op.execute("drop materialized view if exists mv_facility_all;")
