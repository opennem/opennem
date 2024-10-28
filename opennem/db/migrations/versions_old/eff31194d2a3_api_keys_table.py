# pylint: disable=no-member
"""
API Keys table

Revision ID: eff31194d2a3
Revises: 68559b8eefe6
Create Date: 2021-05-25 04:43:52.093681

"""
import sqlalchemy as sa
from alembic import op

revision = "eff31194d2a3"
down_revision = "68559b8eefe6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("keyid", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("keyid"),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
