# pylint: disable=no-member
"""
Make hash_id the photo primary key

Revision ID: 31b16536ac2e
Revises: 669bfb3b1245
Create Date: 2021-03-10 02:00:26.812359

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "31b16536ac2e"
down_revision = "669bfb3b1245"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("photo", "hash_id", existing_type=sa.TEXT(), nullable=False)
    op.drop_column("photo", "id")


def downgrade() -> None:
    # This probably won't work the other way since it requires the id data
    # and i haven't put that in
    op.add_column(
        "photo",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
    )
    op.alter_column("photo", "hash_id", existing_type=sa.TEXT(), nullable=True)
