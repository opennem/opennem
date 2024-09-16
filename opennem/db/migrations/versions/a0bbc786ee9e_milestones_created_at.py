# pylint: disable=no-member
"""
milestones created_at

Revision ID: a0bbc786ee9e
Revises: f9095c47b93c
Create Date: 2024-09-16 12:41:03.122806

"""
from datetime import datetime
from zoneinfo import ZoneInfo
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'a0bbc786ee9e'
down_revision = 'f9095c47b93c'
branch_labels = None
depends_on = None

interval = datetime.now(ZoneInfo("Australia/Sydney")).replace(microsecond=0)

def upgrade() -> None:
    op.add_column('milestones', sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=True))
    op.execute(
        sa.text("UPDATE milestones SET created_at = :interval").bindparams(interval=interval)
    )
    op.alter_column('milestones', 'created_at', nullable=False)



def downgrade() -> None:
    op.drop_column('milestones', 'created_at')
