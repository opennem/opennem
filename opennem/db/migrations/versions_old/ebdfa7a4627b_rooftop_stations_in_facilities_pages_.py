# pylint: disable=no-member
"""
Rooftop stations in facilities pages approved

Revision ID: ebdfa7a4627b
Revises: 728052f1af82
Create Date: 2021-03-17 12:24:44.105807

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ebdfa7a4627b"
down_revision = "728052f1af82"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update station set approved=TRUE where code LIKE 'ROOFTOP_NEM_%';")


def downgrade() -> None:
    pass
