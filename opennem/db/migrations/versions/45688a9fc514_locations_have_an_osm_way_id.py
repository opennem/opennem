# pylint: disable=no-member
"""
Locations have an osm way id

Revision ID: 45688a9fc514
Revises: fc245eb205ed
Create Date: 2021-03-10 15:58:02.269223

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "45688a9fc514"
down_revision = "fc245eb205ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("location", sa.Column("osm_way_id", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("location", "osm_way_id")
