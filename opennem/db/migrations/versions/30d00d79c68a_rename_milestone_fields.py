# pylint: disable=no-member
"""
rename milestone fields

Revision ID: 30d00d79c68a
Revises: 81ac8f9ca8c5
Create Date: 2024-08-02 09:57:26.268815

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

revision = "30d00d79c68a"
down_revision = "81ac8f9ca8c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestones", sa.Column("aggregate", sa.String(), nullable=False))
    op.add_column("milestones", sa.Column("metric", sa.String(), nullable=True))
    op.add_column("milestones", sa.Column("value_unit", sa.String(), nullable=True))
    op.add_column("milestones", sa.Column("description_long", sa.String(), nullable=True))
    op.alter_column(
        "milestones",
        "interval",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.drop_column("milestones", "record_type")
    op.drop_column("milestones", "record_field")


def downgrade() -> None:
    op.add_column("milestones", sa.Column("record_field", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column(
        "milestones",
        sa.Column(
            "record_type",
            postgresql.ENUM("low", "average", "high", name="milestonetype"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.alter_column(
        "milestones",
        "interval",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )
    op.drop_column("milestones", "description_long")
    op.drop_column("milestones", "value_unit")
    op.drop_column("milestones", "metric")
    op.drop_column("milestones", "aggregate")
