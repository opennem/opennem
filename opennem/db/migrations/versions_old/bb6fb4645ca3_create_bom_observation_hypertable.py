# pylint: disable=no-member
"""Create bom_observation hypertable

Revision ID: bb6fb4645ca3
Revises: 4ee58f229572
Create Date: 2020-10-21 14:20:02.009394

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bb6fb4645ca3"
down_revision = "ad3938cfbd45"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        select create_hypertable(
            'bom_observation',
            'observation_time',
            if_not_exists => TRUE,
            migrate_data => TRUE,
            chunk_time_interval => INTERVAL '4 week'
        )
        """
    )


def downgrade() -> None:
    pass
