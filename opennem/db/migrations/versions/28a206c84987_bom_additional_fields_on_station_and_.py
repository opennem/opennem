# pylint: disable=no-member
"""BOM additional fields on station and observation

Revision ID: 28a206c84987
Revises: 659f03439631
Create Date: 2020-10-09 05:12:59.186661

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "28a206c84987"
down_revision = "659f03439631"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bom_observation", sa.Column("cloud", sa.Text(), nullable=True)
    )
    op.add_column(
        "bom_observation", sa.Column("cloud_type", sa.Text(), nullable=True)
    )
    op.add_column(
        "bom_observation", sa.Column("humidity", sa.Numeric(), nullable=True)
    )
    op.add_column(
        "bom_observation", sa.Column("wind_gust", sa.Numeric(), nullable=True)
    )
    op.add_column(
        "bom_station", sa.Column("altitude", sa.Integer(), nullable=True)
    )


def downgrade():
    op.drop_column("bom_station", "altitude")
    op.drop_column("bom_observation", "wind_gust")
    op.drop_column("bom_observation", "humidity")
    op.drop_column("bom_observation", "cloud_type")
    op.drop_column("bom_observation", "cloud")
