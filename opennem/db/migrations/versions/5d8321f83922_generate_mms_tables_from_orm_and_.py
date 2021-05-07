# pylint: disable=no-member
"""
Generate MMS tables from ORM and migration

Revision ID: 5d8321f83922
Revises: c55917f188a5
Create Date: 2021-05-07 09:48:19.071454

"""

from alembic import op

from opennem.core.loader import load_data

# revision identifiers, used by Alembic.
revision = "5d8321f83922"
down_revision = "c55917f188a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_query = load_data("mms_postgres.sql", from_fixture=True, skip_loaders=True)
    op.execute(sql_query)

    # reset the search path so that alembic can update the migration table
    op.execute("set schema 'public';")


def downgrade() -> None:
    op.execute("drop schema if exists mms cascade;")
