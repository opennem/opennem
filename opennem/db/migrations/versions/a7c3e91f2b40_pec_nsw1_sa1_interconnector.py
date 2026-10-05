"""map the pec nsw1-sa1 interconnector

Project EnergyConnect stage 2 registered the NEM's seventh interconnector, NSW1-SA1, effective
2026-10-01. Dispatch has carried it since the 00:05 interval that day and it lands in
facility_scada, but the flows aggregate inner joins units on interconnector = true, so with no
units row it was dropped from NSW1 and SA1 imports, exports and flow emissions (#650).

Interconnectors have no CMS path, so like the existing six this is a manual row. Positive
METEREDMWFLOW is NSW1 to SA1, matching AEMO's naming of the from region first.

Revision ID: a7c3e91f2b40
Revises: 09fd3c32d33b
Create Date: 2026-10-06
"""

from alembic import op

revision = "a7c3e91f2b40"
down_revision = "09fd3c32d33b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        insert into facilities (code, code_display, name, network_id, network_region, approved)
        values ('NSW1-SA1', 'NSW1-SA1', 'Project EnergyConnect (NSW1-SA1)', 'NEM', 'NSW1', false)
        on conflict (code) do nothing
    """)

    op.execute("""
        insert into units (
            code, code_display, station_id, status_id, dispatch_type, approved,
            interconnector, interconnector_region_from, interconnector_region_to, emissions_factor_co2
        )
        select 'NSW1-SA1', 'NSW1-SA1', f.id, 'operating', 'GENERATOR', false, true, 'NSW1', 'SA1', 0
        from facilities f
        where f.code = 'NSW1-SA1'
        on conflict (code) do nothing
    """)


def downgrade() -> None:
    op.execute("delete from units where code = 'NSW1-SA1' and interconnector = true")
    op.execute(
        "delete from facilities f where f.code = 'NSW1-SA1' and not exists (select 1 from units u where u.station_id = f.id)"
    )
