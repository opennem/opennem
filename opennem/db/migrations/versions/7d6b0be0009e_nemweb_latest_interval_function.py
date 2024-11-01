# pylint: disable=no-member
"""
nemweb latest interval function

Revision ID: 7d6b0be0009e
Revises: 4e3c7aa77c7a
Create Date: 2024-11-08 14:04:39.298455

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '7d6b0be0009e'
down_revision = '4e3c7aa77c7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    query = """
    create or replace function nemweb_latest_interval() RETURNS timestamp
        as $$ select date_trunc('hour', now() at time zone 'AEST')  + date_part('minute', now() at time zone 'AEST')::int / 5 * interval '5 min'; $$
        language sql
        immutable;
    """
    op.execute(query)


def downgrade() -> None:
    pass
