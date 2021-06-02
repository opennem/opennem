# pylint: disable=no-member
"""
Fix lake bonney by merging stations

Revision ID: a65022a04846
Revises: cf90d6fbf89f
Create Date: 2021-06-02 15:29:40.209978

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a65022a04846"
down_revision = "cf90d6fbf89f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "update facility set station_id=(select id from station where code='LBBESS') where station_id in (select id from station where code in ('LKBONNY1', 'LKBONNY_2', 'LKBONNY3'));"
    )
    op.execute("delete from station where code in ('LKBONNY1', 'LKBONNY_2', 'LKBONNY3');")


def downgrade() -> None:
    pass
