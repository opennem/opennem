# pylint: disable=no-member
"""
Create stats hypertable

Revision ID: 43f1d539490f
Revises: 889a1453be90
Create Date: 2021-01-05 17:27:45.071634

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "43f1d539490f"
down_revision = "889a1453be90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "select create_hypertable('stats', 'stat_date', migrate_data=>true, if_not_exists=>true)"
    )


def downgrade() -> None:
    pass
