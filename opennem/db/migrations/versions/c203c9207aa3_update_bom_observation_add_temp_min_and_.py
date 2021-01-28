# pylint: disable=no-member
"""
update bom_observation add temp_min and temp_max

Revision ID: c203c9207aa3
Revises: f048f1d8922c
Create Date: 2021-01-28 20:10:05.686924

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c203c9207aa3"
down_revision = "f048f1d8922c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bom_observation", sa.Column("temp_max", sa.Numeric(), nullable=True))
    op.add_column("bom_observation", sa.Column("temp_min", sa.Numeric(), nullable=True))


def downgrade() -> None:
    op.drop_column("bom_observation", "temp_min")
    op.drop_column("bom_observation", "temp_max")
