# pylint: disable=no-member
"""
Remove revisions table old format

Revision ID: c12510c75208
Revises: 5d8321f83922
Create Date: 2021-05-07 00:02:13.760796

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c12510c75208"
down_revision = "5d8321f83922"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("revisions")


def downgrade() -> None:
    op.create_table(
        "revisions",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("station_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("facility_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("location_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "changes",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "previous",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("is_update", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("approved", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("approved_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "approved_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("approved_comment", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("discarded", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("discarded_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "discarded_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], name="fk_revision_facility_id"),
        sa.ForeignKeyConstraint(["location_id"], ["location.id"], name="fk_revision_location_id"),
        sa.ForeignKeyConstraint(["station_id"], ["station.id"], name="fk_revision_station_id"),
        sa.PrimaryKeyConstraint("id", name="revisions_pkey"),
    )
