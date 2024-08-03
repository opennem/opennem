# pylint: disable=no-member
"""
clean up old tables, unrequired meta fields, tighten database

Revision ID: ed45788972f5
Revises: a3fa44a8bf4d
Create Date: 2024-01-16 10:16:15.069998

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ed45788972f5"
down_revision = "a3fa44a8bf4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_photo_station_id", table_name="photo", if_exists=True)
    op.drop_index("ix_photo_hash_id", table_name="photo", if_exists=True)
    op.drop_table("photo")
    op.execute("DROP TYPE IF EXISTS photo")
    op.execute("alter table facility_status drop column if exists created_at")
    op.execute("alter table facility_status drop column if exists created_by")
    op.execute("alter table facility_status drop column if exists updated_at")
    op.execute("alter table participant drop column if exists created_at")
    op.execute("alter table participant drop column if exists created_by")
    op.execute("alter table participant drop column if exists updated_at")


def downgrade() -> None:
    op.add_column(
        "participant",
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "participant",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "participant",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "facility_status",
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "facility_status",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "facility_status",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_table(
        "photo",
        sa.Column("station_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("name", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("mime_type", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("original_url", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("data", postgresql.BYTEA(), autoincrement=False, nullable=True),
        sa.Column("width", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("height", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("license_type", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("license_link", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("author", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("author_link", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("processed", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("processed_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "processed_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("approved", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("approved_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "approved_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("hash_id", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("is_primary", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("order", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["station_id"], ["station.id"], name="fk_photos_station_id"),
    )
    op.create_index("ix_photo_hash_id", "photo", ["hash_id"], unique=False)
    op.create_index("idx_photo_station_id", "photo", ["station_id"], unique=False)
