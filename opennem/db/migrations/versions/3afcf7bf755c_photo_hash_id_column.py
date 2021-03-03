# pylint: disable=no-member
"""
Photo hash_id column

Revision ID: 3afcf7bf755c
Revises: 76b7e7c9462a
Create Date: 2021-03-03 03:08:46.494755

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3afcf7bf755c"
down_revision = "76b7e7c9462a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("photo", sa.Column("hash_id", sa.Text(), nullable=True))
    op.create_index(op.f("ix_photo_hash_id"), "photo", ["hash_id"], unique=False)


def downgrade() -> None:
    op.drop_column("photo", "hash_id")
