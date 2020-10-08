"""Network additional timezone_database and offset fields

Revision ID: 3595c70244db
Revises: f04dfaf47b51
Create Date: 2020-10-09 01:05:10.156455

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3595c70244db"
down_revision = "f04dfaf47b51"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("network", sa.Column("offset", sa.Integer(), nullable=True))
    op.add_column(
        "network", sa.Column("timezone_database", sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column("network", "timezone_database")
    op.drop_column("network", "offset")
