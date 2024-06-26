# pylint: disable=no-member
"""BOM station geom

Revision ID: 8bf30c37cb85
Revises: d45e70a09231
Create Date: 2020-10-06 14:27:28.910935

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8bf30c37cb85"
down_revision = "42cdf37a6e3b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bom_station",
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_bom_station_geom",
        "bom_station",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.execute("update bom_station set geom=ST_SetSRID(ST_MakePoint(lng, lat), 4326);")
    op.drop_column("bom_station", "lng")
    op.drop_column("bom_station", "lat")


def downgrade():
    op.add_column(
        "bom_station",
        sa.Column("lat", sa.NUMERIC(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "bom_station",
        sa.Column("lng", sa.NUMERIC(), autoincrement=False, nullable=True),
    )
    op.drop_index("idx_bom_station_geom", table_name="bom_station")
    op.drop_column("bom_station", "geom")
