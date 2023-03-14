# pylint: disable=no-member
"""
default api key

Revision ID: efb63b1a723d
Revises: eff31194d2a3
Create Date: 2021-05-25 04:45:31.682722

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "efb63b1a723d"
down_revision = "eff31194d2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("insert into api_keys (keyid, description, revoked) values ('DQwfwdHCzjBmnM5yMgkAVg', 'opennem default', FALSE);")


def downgrade() -> None:
    pass
