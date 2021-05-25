# pylint: disable=no-member
"""
Feedback table

Revision ID: 68559b8eefe6
Revises: 0e87606a7f36
Create Date: 2021-05-25 03:08:28.609271

"""
import sqlalchemy as sa
from alembic import op

revision = "68559b8eefe6"
down_revision = "0e87606a7f36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("twitter", sa.Text(), nullable=True),
        sa.Column("user_ip", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("feedback")
