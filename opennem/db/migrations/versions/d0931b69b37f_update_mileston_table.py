# pylint: disable=no-member
"""
Update mileston table

Revision ID: d0931b69b37f
Revises: 4e4fb94633e6
Create Date: 2023-12-12 07:44:02.310785

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d0931b69b37f"
down_revision = "4e4fb94633e6"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # milestone_enum.create(op.get_bind(), checkfirst=True)
    op.execute("DROP TYPE if exists milestonetype cascade")
    op.execute("drop table if exists milestones cascade")

    op.execute('CREATE EXTENSION if not exists "uuid-ossp"')
    op.create_table(
        "milestones",
        sa.Column(
            "instance_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("record_id", sa.Text(), nullable=False),
        sa.Column("dtime", sa.DateTime(), nullable=False),
        sa.Column(
            "record_type",
            sa.Enum(
                "low",
                "average",
                "high",
                name="milestonetype",
            ),
            nullable=False,
        ),
        sa.Column("significance", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("network_id", sa.Text(), nullable=True),
        sa.Column("fueltech_id", sa.Text(), nullable=True),
        sa.Column("fueltech_group_id", sa.Text(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fueltech_group_id"],
            ["fueltech_group.code"],
        ),
        sa.ForeignKeyConstraint(
            ["fueltech_id"],
            ["fueltech.code"],
        ),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
        ),
        sa.PrimaryKeyConstraint("instance_id", "record_id"),
    )
    op.create_index(op.f("ix_milestones_dtime"), "milestones", ["dtime"], unique=False)
    op.drop_constraint("fk_facility_station_code", "facility", type_="foreignkey")
    op.create_foreign_key(
        "fk_facility_station_code",
        "facility",
        "station",
        ["station_id"],
        ["id"],
    )
    op.drop_index("ix_station_code", table_name="station")
    op.create_index(op.f("ix_station_code"), "station", ["code"], unique=True)


def downgrade() -> None:
    op.create_index("ix_stats_date", "stats", [sa.text("stat_date DESC")], unique=False)
    op.create_index(
        "ix_stats_country_type",
        "stats",
        ["stat_type", "country"],
        unique=False,
    )
    op.drop_index(op.f("ix_station_code"), table_name="station")
    op.create_index("ix_station_code", "station", ["code"], unique=False)
    op.drop_constraint("fk_facility_station_code", "facility", type_="foreignkey")
    op.create_foreign_key(
        "fk_facility_station_code",
        "facility",
        "station",
        ["station_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_index(op.f("ix_milestones_dtime"), table_name="milestones")
    op.drop_table("milestones")
    op.execute("DROP TYPE if exists milestonetype cascade")
