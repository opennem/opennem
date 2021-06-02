# pylint: disable=no-member
"""
Set alert_sent field on feedback

Revision ID: cf90d6fbf89f
Revises: 5bf4716b7da9
Create Date: 2021-06-02 07:45:01.780224

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cf90d6fbf89f"
down_revision = "5bf4716b7da9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("feedback", sa.Column("alert_sent", sa.Boolean(), nullable=False))


def downgrade() -> None:
    op.drop_column("feedback", "alert_sent")
