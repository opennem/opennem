# pylint: disable=no-member
"""
trim facility scada table

Revision ID: 338b893d068b
Revises: 615d07cea9ec
Create Date: 2024-01-10 02:11:10.516705

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "338b893d068b"
down_revision = "615d07cea9ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("facility_scada", "created_at")
    op.drop_column("facility_scada", "updated_at")
    op.drop_column("facility_scada", "created_by")


def downgrade() -> None:
    op.add_column(
        "facility_scada",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "facility_scada",
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "facility_scada",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
