# pylint: disable=no-member
"""
dudetail maxrateofchange fields nullable

Revision ID: 1825bf65f16a
Revises: 2c915e2291c4
Create Date: 2021-08-29 20:02:33.944665

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1825bf65f16a"
down_revision = "2c915e2291c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "dudetail", "maxrateofchangeup", existing_type=sa.Numeric(), nullable=True, schema="mms"
    )
    op.alter_column(
        "dudetail", "maxrateofchangedown", existing_type=sa.Numeric(), nullable=True, schema="mms"
    )


def downgrade() -> None:
    op.alter_column(
        "dudetail", "maxrateofchangeup", existing_type=sa.Numeric(), nullable=False, schema="mms"
    )
    op.alter_column(
        "dudetail", "maxrateofchangedown", existing_type=sa.Numeric(), nullable=False, schema="mms"
    )
