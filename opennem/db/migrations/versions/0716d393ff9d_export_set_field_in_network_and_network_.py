# pylint: disable=no-member
"""export_set field in network and network region

Revision ID: 0716d393ff9d
Revises: 0bd670d87da9
Create Date: 2020-11-17 02:07:16.413677

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0716d393ff9d"
down_revision = "0bd670d87da9"
branch_labels = None
depends_on = None


def upgrade():
    # network table
    op.add_column(
        "network", sa.Column("export_set", sa.Boolean(), nullable=True)
    )
    op.execute("UPDATE network set export_set=True")
    op.alter_column("network", "export_set", nullable=False)

    # network region table
    op.add_column(
        "network_region", sa.Column("export_set", sa.Boolean(), nullable=True)
    )
    op.execute("UPDATE network_region set export_set=True")
    op.alter_column("network_region", "export_set", nullable=False)


def downgrade():
    op.drop_column("network_region", "export_set")
    op.drop_column("network", "export_set")
