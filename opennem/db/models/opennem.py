"""
OpenNEM primary schema adapted to support multiple energy sources
"""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from shapely import wkb
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opennem.schema.core import BaseConfig

Base = declarative_base()
metadata = Base.metadata


class FacilitySeenRange(BaseConfig):
    date_start: datetime | None = None
    date_end: datetime | None = None


# db models
class BaseModel:
    """
    Base model for both NEM and WEM
    """

    created_by = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    subject = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    twitter = Column(Text, nullable=True)
    user_ip = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    alert_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CrawlMeta(Base):
    __tablename__ = "crawl_meta"

    spider_name = Column(Text, nullable=False, primary_key=True)
    data = Column(MutableDict.as_mutable(JSONB), nullable=True, index=True)  # type: ignore
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CrawlerSource(enum.Enum):
    nemweb = "nemweb"
    wem = "wem"


class CrawlHistory(Base):
    __tablename__ = "crawl_history"

    source = Column(Enum(CrawlerSource), nullable=False, primary_key=True, default=CrawlerSource.nemweb)
    crawler_name = Column(Text, nullable=False, primary_key=True)
    network_id = Column(Text, ForeignKey("network.code", name="fk_crawl_info_network_code"), primary_key=True, nullable=False)
    interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    inserted_records = Column(Integer, nullable=True)
    crawled_time = Column(DateTime(timezone=True), server_default=func.now())
    processed_time = Column(DateTime(timezone=True), server_default=func.now())

    network = relationship("Network", lazy="joined")


class FuelTechGroup(Base, BaseModel):
    __tablename__ = "fueltech_group"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    color = Column(Text, nullable=True)
    renewable: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


class FuelTech(Base, BaseModel):
    __tablename__ = "fueltech"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    renewable = Column(Boolean, default=False)
    fueltech_group_id = Column(Text, ForeignKey("fueltech_group.code"), nullable=True)

    __table_args__ = (Index("idx_fueltech_code", "code"),)


class Stats(Base, BaseModel):
    __tablename__ = "stats"

    stat_date = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    country = Column(Text, nullable=False, primary_key=True)
    stat_type = Column(Text, nullable=False, primary_key=True)
    value = Column(Numeric(precision=10, scale=4), nullable=True)


class Network(Base, BaseModel):
    __tablename__ = "network"

    code = Column(Text, primary_key=True)
    country = Column(Text, nullable=False)
    label = Column(Text, nullable=True)
    timezone = Column(Text, nullable=False)
    timezone_database = Column(Text, nullable=True)
    offset = Column(Integer, nullable=True)
    interval_size = Column(Integer, nullable=False)
    data_start_date = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    data_end_date = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    network_price = Column(Text, nullable=False)
    interval_shift = Column(Integer, nullable=False, default=0)
    export_set = Column(Boolean, default=True, nullable=False)

    # regions = relationship("NetworkRegion", primaryjoin="NetworkRegion.network_id == Network.code", lazy="joined")

    __table_args__ = (Index("idx_network_code", "code"),)


class NetworkRegion(Base, BaseModel):
    __tablename__ = "network_region"

    network_id = Column(Text, ForeignKey("network.code", name="fk_network_region_network_code"), primary_key=True, nullable=False)
    code = Column(Text, primary_key=True)
    timezone = Column(Text, nullable=True)
    timezone_database = Column(Text, nullable=True)
    offset = Column(Integer, nullable=True)
    export_set = Column(Boolean, default=True, nullable=False)

    # network = relationship("Network", back_populates="regions")


class FacilityStatus(Base):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class BomStation(Base):
    __tablename__ = "bom_station"

    code: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    state: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    web_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_alias: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered: Mapped[datetime | None] = mapped_column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    is_capital: Mapped[bool] = mapped_column(Boolean, default=False)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    altitude: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geom = Column(Geometry("POINT", srid=4326, spatial_index=False))

    __table_args__ = (
        Index("idx_bom_station_geom", "geom", postgresql_using="gist"),
        Index("idx_bom_station_priority", "priority", postgresql_using="btree"),
    )

    @hybrid_property
    def lat(self) -> float | None:
        if self.geom:  # type: ignore
            return wkb.loads(bytes(self.geom.data)).y  # type: ignore
        return None

    @hybrid_property
    def lng(self) -> float | None:
        if self.geom:  # type: ignore
            return wkb.loads(bytes(self.geom.data)).x  # type: ignore
        return None


class BomObservation(Base):
    __tablename__ = "bom_observation"

    observation_time = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    station_id = Column(Text, ForeignKey("bom_station.code", name="fk_bom_observation_station_code"), primary_key=True)
    temp_apparent = Column(Numeric)
    temp_air = Column(Numeric)
    temp_min = Column(Numeric)
    temp_max = Column(Numeric)
    press_qnh = Column(Numeric)
    wind_dir = Column(Text, nullable=True)
    wind_spd = Column(Numeric)
    wind_gust = Column(Numeric)
    humidity = Column(Numeric, nullable=True)
    cloud = Column(Text, nullable=True)
    cloud_type = Column(Text, nullable=True)

    station = relationship("BomStation")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    code: Mapped[str] = mapped_column(Text, index=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text)
    network_id: Mapped[str] = mapped_column(Text, nullable=False)
    network_region: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wikipedia_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    wikidata_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    npi_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)  # NPI facility ID
    osm_way_id: Mapped[str | None] = mapped_column(Text, nullable=True)  # OpenStreetMap Way ID
    location = Column(Geometry("POINT", srid=4326), nullable=True)  # PostGIS location point

    units: Mapped[list["Unit"]] = relationship("Unit", innerjoin=True, lazy="selectin")

    cms_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    cms_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cms_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("code", name="excl_station_network_duid"),)

    def __str__(self) -> str:
        return f"{self.name} <{self.code}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.name} <{self.code}>"

    @hybrid_property
    def unit_codes(self) -> list[str]:
        return list({str(f.code) for f in self.units})

    @hybrid_property
    def scada_range(self) -> FacilitySeenRange | None:
        fsr = FacilitySeenRange(date_start=None, date_end=None)
        if not self.units:
            return fsr
        first_seens = [f.data_first_seen for f in self.units if f.data_first_seen]
        last_seens = [f.data_last_seen for f in self.units if f.data_last_seen]
        if first_seens:
            fsr.date_start = min(first_seens)
        if last_seens:
            fsr.date_end = max(last_seens)
        return fsr


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    code = Column(Text, index=True, nullable=False, unique=True)
    fueltech_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("fueltech.code", name="fk_unit_fueltech_code"), nullable=True
    )
    status_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("facility_status.code", name="fk_unit_facility_status_code"), nullable=True
    )
    station_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("facilities.id", name="fk_unit_facility_id"), nullable=True
    )
    dispatch_type: Mapped[str] = mapped_column(Text, nullable=False, default="GENERATOR")
    capacity_registered: Mapped[float | None] = mapped_column(Numeric(precision=16, scale=4), nullable=True)
    capacity_maximum: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )  # Maximum capacity in MW
    capacity_storage: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )  # Storage capacity in MWh
    registered: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deregistered: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    emissions_factor_co2: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    emission_factor_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    interconnector: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    interconnector_region_to: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    interconnector_region_from: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    data_first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    data_last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    commencement_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    commencement_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, year
    closure_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    closure_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, year
    expected_operation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    expected_operation_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, quarter, year
    expected_operation_date_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_closure_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    expected_closure_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, quarter, year
    expected_closure_date_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_closure_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Construction fields
    construction_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    construction_start_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, year
    construction_start_date_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    construction_cost: Mapped[float | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)  # $ AUD Millions
    construction_cost_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Project approval fields
    project_approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    project_approval_date_specificity: Mapped[str | None] = mapped_column(Text, nullable=True)  # day, month, year
    project_approval_date_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_approval_lodgement_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    cms_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    cms_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cms_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    facility = relationship("Facility", innerjoin=True, back_populates="units", lazy="selectin")
    history = relationship("UnitHistory", back_populates="unit", order_by="UnitHistory.changed_at.desc()", lazy="selectin")

    __table_args__ = (
        Index("idx_facility_station_id", "station_id", postgresql_using="btree"),
        Index("idx_facility_fueltech_id", "fueltech_id"),
        Index(
            "idx_units_lookup",
            code,
            fueltech_id,
            postgresql_where=text(
                "(fueltech_id IS NOT NULL) AND "
                "(fueltech_id <> ALL (ARRAY['imports'::text, 'exports'::text, 'interconnector'::text]))"
            ),
        ),
    )

    def __str__(self) -> str:
        return f"{self.code} <{self.fueltech_id}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.code} <{self.fueltech_id}>"


class UnitHistory(Base, BaseModel):
    """
    Tracks historical changes to unit fields.

    This table stores the history of changes to specific unit fields over time.
    NULL values in tracked fields indicate no change to that field in this history entry.
    """

    __tablename__ = "unit_history"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("units.id", name="fk_unit_history_unit_id", ondelete="CASCADE"), nullable=False, index=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    changed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tracked fields - NULL means no change to this field
    capacity_registered: Mapped[float | None] = mapped_column(Numeric(precision=16, scale=4), nullable=True)
    emissions_factor_co2: Mapped[float | None] = mapped_column(Numeric(precision=16, scale=4), nullable=True)
    emission_factor_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    unit = relationship("Unit", back_populates="history")

    __table_args__ = (Index("idx_unit_history_unit_id_changed_at", "unit_id", "changed_at"),)

    def __str__(self) -> str:
        return f"<UnitHistory: unit_id={self.unit_id} changed_at={self.changed_at}>"

    def __repr__(self) -> str:
        return f"{self.__class__} unit_id={self.unit_id} changed_at={self.changed_at}"


class FacilityScada(Base):
    __tablename__ = "facility_scada"

    interval = Column(TIMESTAMP(timezone=False), index=True, primary_key=True, nullable=False)
    network_id = Column(Text, primary_key=True, nullable=False, index=True)
    facility_code = Column(Text, nullable=False, primary_key=True, index=True)
    generated: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    is_forecast = Column(Boolean, default=False, primary_key=True)
    energy: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    energy_storage: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    energy_quality_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        # 1. Primary Index for Time Bucketing
        Index(
            "idx_facility_scada_interval_bucket",
            interval,
            network_id,
            facility_code,
            is_forecast,
            postgresql_using="btree",
        ),
        # 2. Partial Index for Forecast Filter
        Index(
            "idx_facility_scada_non_forecast",
            interval,
            facility_code,
            generated,
            energy,
            postgresql_where=text("is_forecast = false"),
            postgresql_using="btree",
        ),
        # 3. Index for Grouping
        Index("idx_facility_scada_grouping", network_id, facility_code, energy, postgresql_using="btree"),
        # Existing indexes kept for compatibility
        Index("idx_facility_scada_facility_code_interval", facility_code, interval.desc()),
        Index("idx_facility_scada_network_id", network_id),
        Index("idx_facility_scada_interval_facility_code", interval, facility_code),
        Index(
            "idx_facility_scada_lookup",
            interval,
            facility_code,
            is_forecast,
            postgresql_where=text("is_forecast = false"),
            postgresql_using="btree",
        ),
    )

    def __str__(self) -> str:
        return f"<{self.__class__}: {self.interval} {self.network_id} {self.facility_code}>"

    def __repr__(self) -> str:
        return f"{self.__class__}: {self.interval} {self.network_id} {self.facility_code}"


class BalancingSummary(Base):
    __tablename__ = "balancing_summary"

    network_id = Column(Text, primary_key=True)
    interval: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), index=True, primary_key=True)
    network_region = Column(Text, primary_key=True, index=True)
    forecast_load: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    generation_scheduled: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    generation_non_scheduled: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    generation_total: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    net_interchange: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    demand: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    demand_total: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    price_dispatch: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    net_interchange_trading: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    is_forecast = Column(Boolean, default=False, nullable=False, primary_key=True)
    ss_solar_uigf: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    ss_solar_clearedmw: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    ss_wind_uigf: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    ss_wind_clearedmw: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)

    __table_args__ = (
        Index(
            "idx_balancing_summary_interval_network_region",
            text("interval DESC"),
            network_id,
            network_region,
        ),
        # 1. Primary Index optimized for time bucket operations and filtering
        Index("idx_balancing_time_lookup", interval, network_id, network_region, is_forecast, postgresql_using="btree"),
        # 2. Partial index for non-forecast records with price
        # This helps with the LOCF operation on price
        Index(
            "idx_balancing_price_lookup",
            interval,
            network_id,
            network_region,
            price,
            postgresql_where=text("is_forecast = false AND price IS NOT NULL"),
            postgresql_using="btree",
        ),
        # 3. Index for region-based querying
        Index("idx_balancing_region_time", network_region, interval, is_forecast, postgresql_using="btree"),
    )


class AggregateNetworkFlows(Base):
    __tablename__ = "at_network_flows"

    interval = Column(TIMESTAMP(timezone=False), index=True, primary_key=True, nullable=False)
    network_id = Column(
        Text, ForeignKey("network.code", name="fk_at_network_flows_network_code"), primary_key=True, index=True, nullable=False
    )
    network_region = Column(Text, index=True, primary_key=True, nullable=False)
    energy_imports = Column(Numeric, nullable=True)
    energy_exports = Column(Numeric, nullable=True)
    market_value_imports = Column(Numeric, nullable=True)
    market_value_exports = Column(Numeric, nullable=True)
    emissions_imports = Column(Numeric, nullable=True)
    emissions_exports = Column(Numeric, nullable=True)

    network = relationship("Network")

    __table_args__ = (
        Index("idx_at_network_flows_network_id_trading_interval", "network_id", "interval", postgresql_using="btree"),
        Index("idx_at_network_flows_trading_interval_facility_code", "interval", "network_id", "network_region"),
    )


class AggregateNetworkDemand(Base):
    __tablename__ = "at_network_demand"

    trading_day = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    network_id = Column(
        Text, ForeignKey("network.code", name="fk_at_facility_daily_network_code"), primary_key=True, nullable=False
    )
    network_region = Column(Text, primary_key=True)
    demand_energy = Column(Numeric, nullable=True)
    demand_market_value = Column(Numeric, nullable=True)

    network = relationship("Network")

    __table_args__ = (
        Index("idx_at_network_demand_network_id_trading_interval", network_id, trading_day, postgresql_using="btree"),
        Index("idx_at_network_demand_trading_interval_network_region", trading_day, network_id, network_region),
        Index(
            "idx_at_network_demand_query_optimization",
            network_id,
            network_region,
            trading_day,
            postgresql_include=["demand_energy", "demand_market_value"],
        ),
    )


class Milestones(Base):
    __tablename__ = "milestones"

    record_id: Mapped[str] = mapped_column(Text, primary_key=True)
    interval: Mapped[datetime] = mapped_column(DateTime(timezone=False), primary_key=True)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    aggregate = Column(String, nullable=False)
    metric = Column(String, nullable=True)
    period = Column(String, nullable=True)
    significance = Column(Integer, nullable=False, default=0)
    value: Mapped[float] = mapped_column(Numeric(precision=20, scale=6), nullable=False)
    pct_change: Mapped[float | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)
    value_unit = Column(String, nullable=True)
    network_id = Column(Text, ForeignKey("network.code"), nullable=True)
    network_region: Mapped[str | None] = mapped_column(Text, nullable=True)
    fueltech_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    description_long: Mapped[str] = mapped_column(String, nullable=True)
    previous_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    __table_args__ = (
        Index("idx_milestone_network_id", "network_id", postgresql_using="btree"),
        Index("idx_milestone_fueltech_id", "fueltech_id", postgresql_using="btree"),
        Index("ix_milestones_interval", interval),
        Index("ix_milestones_record_id", record_id),
    )


class AEMOMarketNotice(Base):
    __tablename__ = "aemo_market_notices"

    notice_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, primary_key=True)
    notice_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class FacilityAggregate(Base):
    """Stores aggregated facility data with pricing and emissions calculations"""

    __tablename__ = "at_facility_intervals"

    # Primary key columns
    interval: Mapped[datetime] = mapped_column(DateTime(timezone=False), primary_key=True, nullable=False)
    network_id: Mapped[str] = mapped_column(
        Text, ForeignKey("network.code", name="fk_facility_aggregates_network_code"), primary_key=True, nullable=False, index=True
    )
    facility_code: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False, index=True)
    unit_code: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False, index=True)

    # Data columns
    fueltech_code: Mapped[str | None] = mapped_column(Text, nullable=False)
    network_region: Mapped[str] = mapped_column(Text, nullable=False)
    status_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    energy: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    emissions: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    emissions_intensity: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    market_value: Mapped[float | None] = mapped_column(Numeric(precision=20, scale=6), nullable=True)

    # Metadata
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    __table_args__ = (
        Index("at_facility_intervals_interval_idx", interval.desc()),
        Index("idx_at_facility_intervals_interval_network", interval.desc(), network_id),
        Index("idx_at_facility_intervals_facility_interval", facility_code, interval.desc()),
        Index("idx_at_facility_intervals_network_region", network_region),
        Index(
            "idx_facility_intervals_monthly_agg",
            network_id,
            interval,
            fueltech_code,
            postgresql_where=text(
                "network_id = ANY (ARRAY['NEM'::text, 'AEMO_ROOFTOP'::text, 'OPENNEM_ROOFTOP_BACKFILL'::text])"
            ),
            postgresql_include=["energy", "market_value", "emissions"],
        ),
        Index(
            "idx_facility_intervals_region_monthly_agg",
            network_id,
            network_region,
            interval,
            fueltech_code,
            postgresql_where=text(
                "network_id = ANY (ARRAY['NEM'::text, 'AEMO_ROOFTOP'::text, 'OPENNEM_ROOFTOP_BACKFILL'::text])"
            ),
            postgresql_include=["energy", "market_value", "emissions"],
        ),
        # Index for time bucket operations
        Index(
            "idx_at_facility_intervals_time_facility",
            interval.desc(),
            facility_code,
        ),
        # Index for unit code grouping
        Index(
            "idx_at_facility_intervals_unit_time",
            unit_code,
            interval.desc(),
        ),
    )
