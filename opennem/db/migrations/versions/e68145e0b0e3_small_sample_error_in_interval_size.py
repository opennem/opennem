# pylint: disable=no-member
"""Small sample error in interval size

Revision ID: e68145e0b0e3
Revises: 346125ed062a
Create Date: 2020-10-31 02:03:05.421703

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e68145e0b0e3"
down_revision = "346125ed062a"
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
        if sample_count > 0 then
            return extract(epoch FROM bucket_interval::interval) / 60 / (sample_count - 1);
        end if;

        return 0;
    end;
    $$;

    """
    )


def downgrade():
    pass
