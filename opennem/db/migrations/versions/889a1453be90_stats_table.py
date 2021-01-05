# pylint: disable=no-member
"""
Stats table

Revision ID: 889a1453be90
Revises: b30e47defd26
Create Date: 2021-01-05 16:18:59.833323

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "889a1453be90"
down_revision = "b30e47defd26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stats",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "stat_date", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("stat_type", sa.Text(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.PrimaryKeyConstraint("stat_date", "country", "stat_type"),
    )
    op.create_index(
        op.f("ix_stats_stat_date"), "stats", ["stat_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_stats_stat_date"), table_name="stats")
    op.drop_table("stats")
