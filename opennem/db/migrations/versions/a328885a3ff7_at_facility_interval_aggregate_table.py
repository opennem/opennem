# pylint: disable=no-member
"""
at_facility_interval aggregate table

Revision ID: a328885a3ff7
Revises: e167bf2a27e2
Create Date: 2024-12-02 10:22:21.859458

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a328885a3ff7'
down_revision = 'e167bf2a27e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        SELECT create_hypertable(
            'at_facility_intervals',
            'interval',
            if_not_exists => TRUE,
            migrate_data => TRUE
        );
    """)


def downgrade() -> None:
    pass
