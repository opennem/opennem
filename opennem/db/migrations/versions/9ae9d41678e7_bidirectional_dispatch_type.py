# pylint: disable=no-member
"""
bidirectional dispatch_type

Revision ID: 9ae9d41678e7
Revises: a0bbc786ee9e
Create Date: 2024-10-01 15:47:36.320512

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9ae9d41678e7'
down_revision = 'a0bbc786ee9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # update the dispatchtype type in the database to include BIDIRECTIONAL
    op.execute("CREATE TYPE dispatch_type AS ENUM ('GENERATOR', 'LOAD', 'BIDIRECTIONAL');")
    op.execute("ALTER TABLE facility ALTER COLUMN dispatch_type TYPE dispatch_type USING dispatch_type::text::dispatch_type;")
    op.execute("drop type dispatchtype;")

def downgrade() -> None:
    pass
