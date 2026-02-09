# pylint: disable=no-member
"""
add code_display to facilities and units

Revision ID: f9fb1be73cee
Revises: b443948c1a49
Create Date: 2026-02-09 21:19:16.712014

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f9fb1be73cee"
down_revision = "b443948c1a49"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add code_display columns
    op.add_column("facilities", sa.Column("code_display", sa.Text(), nullable=True))
    op.add_column("units", sa.Column("code_display", sa.Text(), nullable=True))

    # Fix existing "0"-prefixed synthetic codes:
    # 1. Save original code to code_display, strip "0" prefix from code
    #    Pattern ^0[A-Z] targets only synthetic DUIDs (0 + uppercase letter)
    #    Skip if stripping would collide with an existing code
    op.execute("""
        UPDATE units
        SET code_display = code, code = substring(code from 2)
        WHERE code ~ '^0[A-Z]'
        AND substring(code from 2) NOT IN (SELECT code FROM units WHERE code !~ '^0[A-Z]')
    """)
    op.execute("""
        UPDATE facilities
        SET code_display = code, code = substring(code from 2)
        WHERE code ~ '^0[A-Z]'
        AND substring(code from 2) NOT IN (SELECT code FROM facilities WHERE code !~ '^0[A-Z]')
    """)

    # 2. Set code_display = code for all remaining records without code_display
    op.execute("UPDATE units SET code_display = code WHERE code_display IS NULL")
    op.execute("UPDATE facilities SET code_display = code WHERE code_display IS NULL")


def downgrade() -> None:
    # Restore "0"-prefixed codes from code_display before dropping columns
    op.execute("""
        UPDATE units SET code = code_display
        WHERE code_display IS NOT NULL AND code_display ~ '^0[A-Z]'
    """)
    op.execute("""
        UPDATE facilities SET code = code_display
        WHERE code_display IS NOT NULL AND code_display ~ '^0[A-Z]'
    """)

    op.drop_column("units", "code_display")
    op.drop_column("facilities", "code_display")
