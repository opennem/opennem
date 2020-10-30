"""account for one sample in energy_sum

Revision ID: d8e3e95a80d1
Revises: e68145e0b0e3
Create Date: 2020-10-31 02:09:35.285592

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8e3e95a80d1"
down_revision = "e68145e0b0e3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create or replace function interval_size(bucket_interval text, sample_count numeric)
        returns numeric
        immutable
        language plpgsql
        as $$
        begin
            if sample_count > 1 then
                return extract(epoch FROM bucket_interval::interval) / 60 / (sample_count - 1);
            end if;

            if sample_count = 1 then
                return extract(epoch FROM bucket_interval::interval) / 60;
            end if;

            return 0;
        end;
        $$;

    """
    )


def downgrade():
    pass
