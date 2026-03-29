"""Drop redundant facility_scada indexes

facility_scada has 11 indexes consuming 344 GB (4.4x the 78 GB data).
8 are redundant — covered by PK or overlapping composites.

Keep:
- pk_facility_scada (interval, network_id, facility_code, is_forecast) UNIQUE
- idx_facility_scada_facility_code_interval (facility_code, interval DESC)
- idx_facility_scada_interval_facility_code (interval, facility_code)

Drop (saves ~250 GB):
- idx_facility_scada_interval_bucket — same columns as PK
- ix_facility_scada_interval — prefix of PK
- ix_facility_scada_network_id — duplicate of idx_ version
- idx_facility_scada_network_id — low selectivity, never used
- ix_facility_scada_facility_code — prefix of facility_code_interval
- idx_facility_scada_lookup — PK covers this
- idx_facility_scada_non_forecast — never used
- idx_facility_scada_grouping — never used

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-03-23
"""

from alembic import op

revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None

_DROP = [
    "idx_facility_scada_interval_bucket",
    "ix_facility_scada_interval",
    "ix_facility_scada_network_id",
    "idx_facility_scada_network_id",
    "ix_facility_scada_facility_code",
    "idx_facility_scada_lookup",
    "idx_facility_scada_non_forecast",
    "idx_facility_scada_grouping",
]


def upgrade() -> None:
    for idx in _DROP:
        op.execute(f"DROP INDEX IF EXISTS {idx}")


def downgrade() -> None:
    op.execute(
        "CREATE INDEX idx_facility_scada_interval_bucket "
        "ON public.facility_scada USING btree (interval, network_id, facility_code, is_forecast)"
    )
    op.execute("CREATE INDEX ix_facility_scada_interval ON public.facility_scada USING btree (interval)")
    op.execute("CREATE INDEX ix_facility_scada_network_id ON public.facility_scada USING btree (network_id)")
    op.execute("CREATE INDEX idx_facility_scada_network_id ON public.facility_scada USING btree (network_id)")
    op.execute("CREATE INDEX ix_facility_scada_facility_code ON public.facility_scada USING btree (facility_code)")
    op.execute(
        "CREATE INDEX idx_facility_scada_lookup "
        "ON public.facility_scada USING btree (interval, facility_code, is_forecast) WHERE (is_forecast = false)"
    )
    op.execute(
        "CREATE INDEX idx_facility_scada_non_forecast "
        "ON public.facility_scada USING btree (interval, facility_code, generated, energy) WHERE (is_forecast = false)"
    )
    op.execute(
        "CREATE INDEX idx_facility_scada_grouping "
        "ON public.facility_scada USING btree (network_id, facility_code, energy)"
    )
