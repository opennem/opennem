# pylint: disable=no-member
"""Make network_region in balancing summary primary

Revision ID: a76e6ff50cda
Revises: 911efdc0c77f
Create Date: 2020-10-07 11:37:59.674373

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a76e6ff50cda"
down_revision = "911efdc0c77f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("alter table balancing_summary drop constraint balancing_summary_pkey")
    op.execute(
        """
        alter table balancing_summary add constraint
        balancing_summary_pkey primary key (trading_interval, network_id, network_region)
        """
    )


def downgrade() -> None:
    op.execute("alter table balancing_summary drop constraint balancing_summary_pkey")
    op.execute(
        """
        alter table balancing_summary add constraint
        balancing_summary_pkey primary key (trading_interval, network_id)
        """
    )
