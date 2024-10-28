# pylint: disable=no-member
"""
update fueltechs distillate wem

Revision ID: 8ab718cb9fde
Revises: 576480e97f8f
Create Date: 2023-04-13 16:01:05.964918

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8ab718cb9fde"
down_revision = "576480e97f8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    update facility set fueltech_id = 'distillate' where code in ('NAMKKN_MERR_SG1', 'KALAMUNDA_SG');
    """
    )


def downgrade() -> None:
    op.execute(
        """
    update facility set fueltech_id = 'gas_ocgt' where code in ('NAMKKN_MERR_SG1', 'KALAMUNDA_SG');

    """
    )
