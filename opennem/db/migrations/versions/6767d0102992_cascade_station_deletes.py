# pylint: disable=no-member
"""
Cascade station deletes

Revision ID: 6767d0102992
Revises: ae504bc24d95
Create Date: 2020-12-24 14:41:58.428764

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "6767d0102992"
down_revision = "ae504bc24d95"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
            alter table public.facility
                drop constraint if exists fk_station_status_code,
                drop constraint if exists fk_facility_station_code,
            add constraint fk_facility_station_code
                foreign key (station_id)
                references station(id)
                on delete cascade;
        """
    )


def downgrade() -> None:
    pass
