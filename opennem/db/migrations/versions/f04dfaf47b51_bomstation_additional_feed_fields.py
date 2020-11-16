# pylint: disable=no-member
"""BOMStation additional feed fields

Revision ID: f04dfaf47b51
Revises: a76e6ff50cda
Create Date: 2020-10-08 01:04:58.796972

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f04dfaf47b51"
down_revision = "a76e6ff50cda"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bom_station", sa.Column("feed_url", sa.Text(), nullable=True)
    )
    op.add_column(
        "bom_station", sa.Column("is_capital", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "bom_station", sa.Column("name_alias", sa.Text(), nullable=True)
    )
    op.add_column(
        "bom_station", sa.Column("priority", sa.Integer(), nullable=True)
    )
    op.add_column(
        "bom_station", sa.Column("website_url", sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column("bom_station", "website_url")
    op.drop_column("bom_station", "priority")
    op.drop_column("bom_station", "name_alias")
    op.drop_column("bom_station", "is_capital")
    op.drop_column("bom_station", "feed_url")
