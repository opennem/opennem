# pylint: disable=no-member
"""
nemweb_latest_interval function

Revision ID: c860e4328b38
Revises: 5b5f4a4957ed
Create Date: 2022-06-23 05:53:35.439930

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c860e4328b38"
down_revision = "5b5f4a4957ed"
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
