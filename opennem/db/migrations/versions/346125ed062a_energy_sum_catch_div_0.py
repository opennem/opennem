# pylint: disable=no-member
"""energy sum catch div/0

Revision ID: 346125ed062a
Revises: 10f1d9517df7
Create Date: 2020-10-29 17:54:38.794461

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "346125ed062a"
down_revision = "10f1d9517df7"
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
            return extract(epoch FROM bucket_interval::interval) / 60 / sample_count;
        end if;

        return 0;
    end;
    $$;

    """
    )


def downgrade():
    pass
