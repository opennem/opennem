# pylint: disable=no-member
"""
fueltech groups

Revision ID: 1f1f506e4d44
Revises: 1341a5d72755
Create Date: 2022-09-22 05:56:33.151562

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1f1f506e4d44"
down_revision = "1341a5d72755"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fueltech_group",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    op.add_column("fueltech", sa.Column("fueltech_group_id", sa.Text(), nullable=True))
    op.create_foreign_key(None, "fueltech", "fueltech_group", ["fueltech_group_id"], ["code"])


def downgrade() -> None:
    op.drop_constraint(None, "fueltech", type_="foreignkey")
    op.drop_column("fueltech", "fueltech_group_id")
    op.drop_table("fueltech_group")
