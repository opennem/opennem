# pylint: disable=no-member
"""
at_network_flows as a hypertable

Revision ID: cbb8705b50ac
Revises: 5c41d50dd9b6
Create Date: 2022-03-10 02:12:28.791060

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "cbb8705b50ac"
down_revision = "5c41d50dd9b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SELECT create_hypertable('at_network_flows','trading_interval', if_not_exists => TRUE, migrate_data=>TRUE);")


def downgrade() -> None:
    pass
