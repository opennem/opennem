# pylint: disable=no-member
"""
merge unit history and cms_id text migrations

Revision ID: 77fcdc3ffe4c
Revises: 07e436912603, 6a5162835014
Create Date: 2025-06-23 03:48:08.764474

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '77fcdc3ffe4c'
down_revision = ('07e436912603', '6a5162835014')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
