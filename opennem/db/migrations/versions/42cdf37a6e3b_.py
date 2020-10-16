"""This is the base migration as of this date. Don't touch this.

Revision ID: 42cdf37a6e3b
Revises:
Create Date: 2020-10-06 13:53:50.693303

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "42cdf37a6e3b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "bom_station",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("registered", sa.Date(), nullable=True),
        sa.Column("lat", sa.Numeric(), nullable=True),
        sa.Column("lng", sa.Numeric(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "facility_status",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "fueltech",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("renewable", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "location",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("address1", sa.Text(), nullable=True),
        sa.Column("address2", sa.Text(), nullable=True),
        sa.Column("locality", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("postcode", sa.Text(), nullable=True),
        sa.Column("place_id", sa.Text(), nullable=True),
        sa.Column("geocode_approved", sa.Boolean(), nullable=True),
        sa.Column("geocode_skip", sa.Boolean(), nullable=True),
        sa.Column("geocode_processed_at", sa.DateTime(), nullable=True),
        sa.Column("geocode_by", sa.Text(), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column(
            "boundary",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_location_boundary",
        "location",
        ["boundary"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "idx_location_geom",
        "location",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        op.f("ix_location_place_id"), "location", ["place_id"], unique=False
    )
    op.create_table(
        "network",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("interval_size", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "participant",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("network_name", sa.Text(), nullable=True),
        sa.Column("network_code", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("abn", sa.Text(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_participant_code"), "participant", ["code"], unique=True
    )
    op.create_table(
        "balancing_summary",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("forecast_load", sa.Numeric(), nullable=True),
        sa.Column("generation_scheduled", sa.Numeric(), nullable=True),
        sa.Column("generation_non_scheduled", sa.Numeric(), nullable=True),
        sa.Column("generation_total", sa.Numeric(), nullable=True),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_balancing_summary_network_code",
        ),
        sa.PrimaryKeyConstraint("network_id", "trading_interval"),
    )
    op.create_index(
        op.f("ix_balancing_summary_trading_interval"),
        "balancing_summary",
        ["trading_interval"],
        unique=False,
    )
    op.create_table(
        "bom_observation",
        sa.Column("observation_time", sa.DateTime(), nullable=False),
        sa.Column("station_id", sa.Text(), nullable=False),
        sa.Column("temp_apparent", sa.Numeric(), nullable=True),
        sa.Column("temp_air", sa.Numeric(), nullable=True),
        sa.Column("press_qnh", sa.Numeric(), nullable=True),
        sa.Column("wind_dir", sa.Text(), nullable=True),
        sa.Column("wind_spd", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["bom_station.code"],
            name="fk_bom_observation_station_code",
        ),
        sa.PrimaryKeyConstraint("observation_time", "station_id"),
    )
    op.create_table(
        "facility_scada",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("facility_code", sa.Text(), nullable=False),
        sa.Column("generated", sa.Numeric(), nullable=True),
        sa.Column("eoi_quantity", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_balancing_summary_network_code",
        ),
        sa.PrimaryKeyConstraint(
            "network_id", "trading_interval", "facility_code"
        ),
    )
    op.create_index(
        op.f("ix_facility_scada_facility_code"),
        "facility_scada",
        ["facility_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_facility_scada_trading_interval"),
        "facility_scada",
        ["trading_interval"],
        unique=False,
    )
    op.create_table(
        "station",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("wikipedia_link", sa.Text(), nullable=True),
        sa.Column("wikidata_id", sa.Text(), nullable=True),
        sa.Column("network_code", sa.Text(), nullable=True),
        sa.Column("network_name", sa.Text(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"], ["location.id"], name="fk_station_location_id"
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["participant.id"],
            name="fk_station_participant_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_station_code"), "station", ["code"], unique=False)
    op.create_index(
        op.f("ix_station_network_code"),
        "station",
        ["network_code"],
        unique=False,
    )
    op.create_table(
        "facility",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("fueltech_id", sa.Text(), nullable=True),
        sa.Column("status_id", sa.Text(), nullable=True),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("network_code", sa.Text(), nullable=True),
        sa.Column("network_region", sa.Text(), nullable=True),
        sa.Column("network_name", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column(
            "dispatch_type",
            sa.Enum("GENERATOR", "LOAD", name="dispatchtype"),
            nullable=False,
        ),
        sa.Column("capacity_registered", sa.Numeric(), nullable=True),
        sa.Column("registered", sa.DateTime(), nullable=True),
        sa.Column("deregistered", sa.DateTime(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("unit_number", sa.Integer(), nullable=True),
        sa.Column("unit_alias", sa.Text(), nullable=True),
        sa.Column("unit_capacity", sa.Numeric(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["fueltech_id"], ["fueltech.code"], name="fk_facility_fueltech_id"
        ),
        sa.ForeignKeyConstraint(
            ["network_id"], ["network.code"], name="fk_station_network_code"
        ),
        sa.ForeignKeyConstraint(
            ["station_id"], ["station.id"], name="fk_station_status_code"
        ),
        sa.ForeignKeyConstraint(
            ["status_id"],
            ["facility_status.code"],
            name="fk_facility_status_code",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_facility_code"), "facility", ["code"], unique=False
    )
    op.create_index(
        op.f("ix_facility_network_code"),
        "facility",
        ["network_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_facility_network_region"),
        "facility",
        ["network_region"],
        unique=False,
    )
    op.create_table(
        "photo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("original_url", sa.Text(), nullable=True),
        sa.Column("data", sa.LargeBinary(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("license_type", sa.Text(), nullable=True),
        sa.Column("license_link", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("author_link", sa.Text(), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=True),
        sa.Column("processed_by", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["station_id"], ["station.id"], name="fk_photos_station_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "revisions",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("facility_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("previous", sa.JSON(), nullable=True),
        sa.Column("is_update", sa.Boolean(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_comment", sa.Text(), nullable=True),
        sa.Column("discarded", sa.Boolean(), nullable=True),
        sa.Column("discarded_by", sa.Text(), nullable=True),
        sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_id"], ["facility.id"], name="fk_revision_facility_id"
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["location.id"], name="fk_revision_location_id"
        ),
        sa.ForeignKeyConstraint(
            ["station_id"], ["station.id"], name="fk_revision_station_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("revisions")
    op.drop_table("photo")
    op.drop_index(op.f("ix_facility_network_region"), table_name="facility")
    op.drop_index(op.f("ix_facility_network_code"), table_name="facility")
    op.drop_index(op.f("ix_facility_code"), table_name="facility")
    op.drop_table("facility")
    op.drop_index(op.f("ix_station_network_code"), table_name="station")
    op.drop_index(op.f("ix_station_code"), table_name="station")
    op.drop_table("station")
    op.drop_index(
        op.f("ix_facility_scada_trading_interval"), table_name="facility_scada"
    )
    op.drop_index(
        op.f("ix_facility_scada_facility_code"), table_name="facility_scada"
    )
    op.drop_table("facility_scada")
    op.drop_table("bom_observation")
    op.drop_index(
        op.f("ix_balancing_summary_trading_interval"),
        table_name="balancing_summary",
    )
    op.drop_table("balancing_summary")
    op.drop_index(op.f("ix_participant_code"), table_name="participant")
    op.drop_table("participant")
    op.drop_table("network")
    op.drop_index(op.f("ix_location_place_id"), table_name="location")
    op.drop_index("idx_location_geom", table_name="location")
    op.drop_index("idx_location_boundary", table_name="location")
    op.drop_table("location")
    op.drop_table("fueltech")
    op.drop_table("facility_status")
    op.drop_table("bom_station")
    # ### end Alembic commands ###
