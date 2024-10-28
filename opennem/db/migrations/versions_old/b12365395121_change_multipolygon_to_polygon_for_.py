# pylint: disable=no-member
"""
Change multipolygon to polygon for boundaries

Revision ID: b12365395121
Revises: 45688a9fc514
Create Date: 2021-03-10 18:03:27.180720

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b12365395121"
down_revision = "45688a9fc514"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("location", "boundary")
    op.add_column(
        "location",
        sa.Column(
            "boundary",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                spatial_index=True,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("location", "boundary")
