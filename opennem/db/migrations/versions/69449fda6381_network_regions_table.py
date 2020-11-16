# pylint: disable=no-member
"""Network regions table

Revision ID: 69449fda6381
Revises: d8e3e95a80d1
Create Date: 2020-11-09 14:42:05.172383

"""
import sqlalchemy as sa
from alembic import op

revision = "69449fda6381"
down_revision = "d8e3e95a80d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "network_region",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=True),
        sa.Column("timezone_database", sa.Text(), nullable=True),
        sa.Column("offset", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_network_region_network_code",
        ),
        sa.PrimaryKeyConstraint("network_id", "code"),
    )


def downgrade():
    op.drop_table("network_region")
