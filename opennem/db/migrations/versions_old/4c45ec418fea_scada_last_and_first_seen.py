# pylint: disable=no-member
"""
Scada last and first seen

Revision ID: 4c45ec418fea
Revises: b12365395121
Create Date: 2021-03-11 12:27:58.286142

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c45ec418fea"
down_revision = "b12365395121"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility",
        sa.Column("data_first_seen", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "facility",
        sa.Column("data_last_seen", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_facility_data_first_seen"),
        "facility",
        ["data_first_seen"],
        unique=False,
    )
    op.create_index(
        op.f("ix_facility_data_last_seen"),
        "facility",
        ["data_last_seen"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_data_last_seen"), table_name="facility")
    op.drop_index(op.f("ix_facility_data_first_seen"), table_name="facility")
    op.drop_column("facility", "data_last_seen")
    op.drop_column("facility", "data_first_seen")
