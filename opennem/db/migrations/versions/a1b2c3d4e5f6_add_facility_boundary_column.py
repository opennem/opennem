# pylint: disable=no-member
"""
add facility boundary column

Revision ID: a1b2c3d4e5f6
Revises: f9fb1be73cee
Create Date: 2026-03-18 12:00:00.000000

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f9fb1be73cee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facilities",
        sa.Column(
            "boundary",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("facilities", "boundary")
