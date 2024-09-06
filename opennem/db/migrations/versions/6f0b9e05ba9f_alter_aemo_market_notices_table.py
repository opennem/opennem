# pylint: disable=no-member
"""
alter aemo_market_notices table

Revision ID: 6f0b9e05ba9f
Revises: a97b307f2b64
Create Date: 2024-09-06 18:36:01.802410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f0b9e05ba9f"
down_revision = "a97b307f2b64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aemo_market_notices",
        sa.Column("notice_id", sa.Integer(), nullable=False),
        sa.Column("notice_type", sa.String(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("issue_date", sa.DateTime(), nullable=False),
        sa.Column("external_reference", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("notice_id"),
    )
    op.create_index(
        op.f("ix_aemo_market_notices_creation_date"), "aemo_market_notices", ["creation_date"], unique=False
    )
    op.create_index(op.f("ix_aemo_market_notices_notice_id"), "aemo_market_notices", ["notice_id"], unique=False)
    op.create_index(op.f("ix_aemo_market_notices_notice_type"), "aemo_market_notices", ["notice_type"], unique=False)



def downgrade() -> None:
    op.drop_index(op.f("ix_aemo_market_notices_notice_type"), table_name="aemo_market_notices")
    op.drop_index(op.f("ix_aemo_market_notices_notice_id"), table_name="aemo_market_notices")
    op.drop_index(op.f("ix_aemo_market_notices_creation_date"), table_name="aemo_market_notices")
    op.drop_table("aemo_market_notices")
