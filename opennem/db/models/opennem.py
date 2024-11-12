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
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    date_min: datetime | None = None
    date_max: datetime | None = None


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
    data = Column(MutableDict.as_mutable(JSONB), nullable=True, index=True)
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
    value = Column(Numeric, nullable=True)


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
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).y
        return None

    @hybrid_property
    def lng(self) -> float | None:
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).x
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
    code = Column(Text, index=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text)
    network_id: Mapped[str] = mapped_column(Text, nullable=False)
    network_region: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wikipedia_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    wikidata_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    units: Mapped[list["Unit"]] = relationship("Unit", innerjoin=True, lazy="selectin")

    __table_args__ = (UniqueConstraint("code", name="excl_station_network_duid"),)

    def __str__(self) -> str:
        return f"{self.name} <{self.code}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.name} <{self.code}>"

    @hybrid_property
    def unit_codes(self) -> list[str]:
        return list({f.code for f in self.units})

    @hybrid_property
    def scada_range(self) -> FacilitySeenRange | None:
        fsr = FacilitySeenRange(date_min=None, date_max=None)
        if not self.units:
            return fsr
        first_seens = [f.data_first_seen for f in self.units if f.data_first_seen]
        last_seens = [f.data_last_seen for f in self.units if f.data_last_seen]
        if first_seens:
            fsr.date_min = min(first_seens)
        if last_seens:
            fsr.date_max = max(last_seens)
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
    capacity_registered: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    registered: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deregistered: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_closure_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_closure_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_alias: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_capacity: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    emissions_factor_co2: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    emission_factor_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    interconnector: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    interconnector_region_to: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    interconnector_region_from: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    data_first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    data_last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    facility = relationship("Facility", innerjoin=True, back_populates="units", lazy="selectin")

    __table_args__ = (
        Index("idx_facility_station_id", "station_id", postgresql_using="btree"),
        Index("idx_facility_fueltech_id", "fueltech_id"),
    )

    def __str__(self) -> str:
        return f"{self.code} <{self.fueltech_id}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.code} <{self.fueltech_id}>"


class FacilityScada(Base):
    __tablename__ = "facility_scada"

    interval = Column(TIMESTAMP(timezone=False), index=True, primary_key=True, nullable=False)
    network_id = Column(Text, primary_key=True, nullable=False, index=True)
    facility_code = Column(Text, nullable=False, primary_key=True, index=True)
    generated = Column(Numeric, nullable=True)
    is_forecast = Column(Boolean, default=False, primary_key=True)
    energy: Mapped[float] = mapped_column(Numeric, nullable=True)
    energy_quality_flag = Column(Numeric, nullable=False, default=0)

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
        # Additional optimization hints
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
    forecast_load = Column(Numeric, nullable=True)
    generation_scheduled = Column(Numeric, nullable=True)
    generation_non_scheduled = Column(Numeric, nullable=True)
    generation_total = Column(Numeric, nullable=True)
    net_interchange = Column(Numeric, nullable=True)
    demand = Column(Numeric, nullable=True)
    demand_total = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
    price_dispatch = Column(Numeric, nullable=True)
    net_interchange_trading = Column(Numeric, nullable=True)
    is_forecast = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        # Index("idx_balancing_summary_network_id_interval", "network_id", "interval", postgresql_using="btree"),
        Index(
            "idx_balancing_summary_interval_network_region",
            "interval",
            "network_id",
            "network_region",
            postgresql_ops={"interval": "DESC"},
        ),
        # 1. Primary Index optimized for time bucket operations and filtering
        Index("idx_balancing_time_lookup", "interval", "network_id", "network_region", "is_forecast", postgresql_using="btree"),
        # 2. Partial index for non-forecast records with price
        # This helps with the LOCF operation on price
        Index(
            "idx_balancing_price_lookup",
            "interval",
            "network_id",
            "network_region",
            "price",
            postgresql_where=text("is_forecast = false AND price IS NOT NULL"),
            postgresql_using="btree",
        ),
        # 3. Index for region-based querying
        Index("idx_balancing_region_time", "network_region", "interval", "is_forecast", postgresql_using="btree"),
    )


class AggregateNetworkFlows(Base):
    __tablename__ = "at_network_flows"

    trading_interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
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
        Index("idx_at_network_flowsy_network_id_trading_interval", "network_id", "trading_interval", postgresql_using="btree"),
        Index("idx_at_network_flows_trading_interval_facility_code", "trading_interval", "network_id", "network_region"),
    )


class AggregateNetworkDemand(Base):
    __tablename__ = "at_network_demand"

    trading_day = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    network_id = Column(
        Text, ForeignKey("network.code", name="fk_at_facility_daily_network_code"), primary_key=True, index=True, nullable=False
    )
    network_region = Column(Text, primary_key=True)
    demand_energy = Column(Numeric, nullable=True)
    demand_market_value = Column(Numeric, nullable=True)

    network = relationship("Network")

    __table_args__ = (
        Index("idx_at_network_demand_network_id_trading_interval", "network_id", "trading_day", postgresql_using="btree"),
        Index("idx_at_network_demand_trading_interval_network_region", "trading_day", "network_id", "network_region"),
    )


class Milestones(Base):
    __tablename__ = "milestones"

    record_id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    interval: Mapped[datetime] = mapped_column(DateTime(timezone=False), primary_key=True, index=True)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    aggregate = Column(String, nullable=False)
    metric = Column(String, nullable=True)
    period = Column(String, nullable=True)
    significance = Column(Integer, nullable=False, default=0)
    value = Column(Float, nullable=False)
    value_unit = Column(String, nullable=True)
    network_id = Column(Text, ForeignKey("network.code"), nullable=True)
    network_region: Mapped[str | None] = mapped_column(Text, nullable=True)
    fueltech_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    description_long: Mapped[str] = mapped_column(String, nullable=True)
    previous_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("record_id", "interval", name="excl_milestone_record_id_interval"),
        Index("idx_milestone_network_id", "network_id", postgresql_using="btree"),
        Index("idx_milestone_fueltech_id", "fueltech_id", postgresql_using="btree"),
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
        Text, ForeignKey("network.code", name="fk_facility_aggregates_network_code"), primary_key=True, nullable=False
    )
    facility_code: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    unit_code: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)

    # Data columns
    fueltech_code: Mapped[str | None] = mapped_column(Text, nullable=False)
    network_region: Mapped[str] = mapped_column(Text, nullable=False)
    status_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    emissions: Mapped[float | None] = mapped_column(Float, nullable=True)
    emissions_intensity: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    __table_args__ = (
        Index("idx_at_facility_intervals_interval_network", interval.desc(), network_id),
        Index("idx_at_facility_intervals_facility_interval", facility_code, interval.desc()),
        Index("idx_at_facility_intervals_network_region", network_region),
    )
