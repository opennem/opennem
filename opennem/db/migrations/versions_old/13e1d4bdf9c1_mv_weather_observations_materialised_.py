# pylint: disable=no-member
"""
mv_weather_observations materialised view

Revision ID: 13e1d4bdf9c1
Revises: ed45788972f5
Create Date: 2024-01-24 00:53:18.488464

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "13e1d4bdf9c1"
down_revision = "ed45788972f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("commit")

    op.execute("""
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weather_observations
with (timescaledb.continuous) as
select
    time_bucket('30m', observation_time) as observation_time,
    station_id as station_id,

    case when min(temp_air) is not null
        then avg(temp_air)
        else NULL
    end as temp_air,

    case when min(temp_min) is not null
        then min(temp_min)
        else min(temp_air)
    end as temp_min,

    case when max(temp_max) is not null
        then max(temp_max)
        else max(temp_air)
    end as temp_max
from bom_observation
group by 1, 2;
"""
    )


def downgrade() -> None:
    op.execute("drop materialized view if exists mv_weather_observations;")
