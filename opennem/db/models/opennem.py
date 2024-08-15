"""
OpenNEM primary schema adapted to support multiple energy sources
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

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
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opennem.core.dispatch_type import DispatchType
from opennem.parsers.aemo.schemas import AEMODataSource
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


class ApiKeys(Base):
    __tablename__ = "api_keys"

    keyid = Column(Text, nullable=False, primary_key=True)
    description = Column(Text, nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
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


class TaskProfile(Base):
    __tablename__ = "task_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(Text, nullable=False)
    time_start = Column(DateTime(timezone=True), nullable=False)
    time_end = Column(DateTime(timezone=True), nullable=True)
    time_sql = Column(DateTime(timezone=True), nullable=True)
    time_cpu = Column(DateTime(timezone=True), nullable=True)
    errors = Column(Integer, default=0, nullable=False)
    retention_period = Column(Text, nullable=True, index=True)
    level = Column(Text, nullable=True, index=True)
    invokee_name = Column(Text, nullable=True, index=True)


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

    facilities = relationship("Facility")

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

    regions = relationship("NetworkRegion", primaryjoin="NetworkRegion.network_id == Network.code", lazy="joined")

    __table_args__ = (Index("idx_network_code", "code"),)


class NetworkRegion(Base, BaseModel):
    __tablename__ = "network_region"

    network_id = Column(Text, ForeignKey("network.code", name="fk_network_region_network_code"), primary_key=True, nullable=False)
    code = Column(Text, primary_key=True)
    timezone = Column(Text, nullable=True)
    timezone_database = Column(Text, nullable=True)
    offset = Column(Integer, nullable=True)
    export_set = Column(Boolean, default=True, nullable=False)

    network = relationship("Network", back_populates="regions")


class FacilityStatus(Base):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class Participant(Base):
    __tablename__ = "participant"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    code = Column(Text, unique=True, index=True)
    name = Column(Text)
    network_name = Column(Text)
    network_code = Column(Text)
    country = Column(Text)
    abn = Column(Text)
    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class BomStation(Base):
    __tablename__ = "bom_station"

    code = Column(Text, primary_key=True)
    state = Column(Text)
    name = Column(Text)
    web_code = Column(Text, nullable=True)
    name_alias = Column(Text, nullable=True)
    registered = Column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    is_capital = Column(Boolean, default=False)
    website_url = Column(Text, nullable=True)
    feed_url = Column(Text, nullable=True)
    altitude = Column(Integer, nullable=True)
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


class Location(Base):
    __tablename__ = "location"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)
    osm_way_id = Column(Text, nullable=True)
    place_id = Column(Text, nullable=True, index=True)
    geocode_approved = Column(Boolean, default=False)
    geocode_skip = Column(Boolean, default=False)
    geocode_processed_at = Column(DateTime, nullable=True)
    geocode_by = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326, spatial_index=False))
    boundary = Column(Geometry("POLYGON", srid=4326, spatial_index=True))

    __table_args__ = (
        Index("idx_location_geom", "geom", postgresql_using="gist"),
        Index("idx_location_boundary", "boundary", postgresql_using="gist"),
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


class Station(Base, BaseModel):
    __tablename__ = "station"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participant.id", name="fk_station_participant_id"), nullable=True)
    location_id = Column(Integer, ForeignKey("location.id", name="fk_station_location_id"), nullable=True)
    code = Column(Text, index=True, nullable=False, unique=True)
    name = Column(Text)
    description = Column(Text, nullable=True)
    wikipedia_link = Column(Text, nullable=True)
    wikidata_id = Column(Text, nullable=True)
    network_code = Column(Text, index=True)
    network_name = Column(Text)
    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    website_url = Column(Text, nullable=True)

    participant = relationship("Participant", cascade="all, delete")
    location = relationship("Location", lazy="joined", innerjoin=False, cascade="all, delete")
    facilities = relationship("Facility", lazy="joined", innerjoin=False, cascade="all, delete")

    __table_args__ = (UniqueConstraint("code", name="excl_station_network_duid"),)

    def __str__(self) -> str:
        return f"{self.name} <{self.code}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.name} <{self.code}>"

    @hybrid_property
    def facility_codes(self) -> list[str]:
        return list({f.code for f in self.facilities})

    @hybrid_property
    def scada_range(self) -> FacilitySeenRange | None:
        fsr = FacilitySeenRange(date_min=None, date_max=None)
        if not self.facilities:
            return fsr
        first_seens = [f.data_first_seen for f in self.facilities if f.data_first_seen]
        last_seens = [f.data_last_seen for f in self.facilities if f.data_last_seen]
        if first_seens:
            fsr.date_min = min(first_seens)
        if last_seens:
            fsr.date_max = max(last_seens)
        return fsr

    @hybrid_property
    def capacity_registered(self) -> float | None:
        cap_reg: float | None = None
        for fac in self.facilities:
            if (
                fac.capacity_registered
                and type(fac.capacity_registered) in [int, float, Decimal]
                and fac.status_id in ["operating", "committed", "commissioning"]
                and fac.dispatch_type == DispatchType.GENERATOR
                and fac.active
            ):
                if not cap_reg:
                    cap_reg = 0
                cap_reg += float(fac.capacity_registered)
        if cap_reg:
            cap_reg = round(cap_reg, 2)
        return cap_reg


class Facility(Base, BaseModel):
    __tablename__ = "facility"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    network_id = Column(Text, ForeignKey("network.code", name="fk_station_network_code"), nullable=False)
    fueltech_id = Column(Text, ForeignKey("fueltech.code", name="fk_facility_fueltech_id"), nullable=True)
    status_id = Column(Text, ForeignKey("facility_status.code", name="fk_facility_status_code"))
    station_id = Column(Integer, ForeignKey("station.id", name="fk_facility_station_code"), nullable=True)
    code = Column(Text, index=True, nullable=False, unique=True)
    network_code = Column(Text, nullable=True, index=True)
    network_region = Column(Text, index=True)
    network_name = Column(Text)
    active = Column(Boolean, default=True)
    dispatch_type: DispatchType = Column(Enum(DispatchType), nullable=False, default=DispatchType.GENERATOR)
    capacity_registered = Column(Numeric, nullable=True)
    registered = Column(DateTime, nullable=True)
    deregistered = Column(DateTime, nullable=True)
    expected_closure_date = Column(DateTime, nullable=True)
    expected_closure_year = Column(Integer, nullable=True)
    unit_id = Column(Integer, nullable=True)
    unit_number = Column(Integer, nullable=True)
    unit_alias = Column(Text, nullable=True)
    unit_capacity = Column(Numeric, nullable=True)
    emissions_factor_co2 = Column(Numeric, nullable=True)
    emission_factor_source = Column(Text, nullable=True)
    interconnector = Column(Boolean, default=False, index=True)
    interconnector_region_to = Column(Text, nullable=True, index=True)
    interconnector_region_from = Column(Text, nullable=True, index=True)
    data_first_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    data_last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    include_in_geojson = Column(Boolean, default=True)

    network = relationship("Network", lazy="joined", innerjoin=True)
    fueltech = relationship("FuelTech", back_populates="facilities", lazy="joined", innerjoin=False)
    status = relationship("FacilityStatus", lazy="joined", innerjoin=True)

    __table_args__ = (
        UniqueConstraint("network_id", "code", name="excl_facility_network_id_code"),
        Index("idx_facility_station_id", "station_id", postgresql_using="btree"),
        Index("idx_facility_fueltech_id", "fueltech_id"),
    )

    def __str__(self) -> str:
        return f"{self.code} <{self.fueltech_id}>"

    def __repr__(self) -> str:
        return f"{self.__class__} {self.code} <{self.fueltech_id}>"


class FacilityScada(Base):
    __tablename__ = "facility_scada"

    network_id = Column(Text, primary_key=True, nullable=False)
    interval = Column(TIMESTAMP(timezone=False), index=True, primary_key=True, nullable=False)
    facility_code = Column(Text, nullable=False, primary_key=True, index=True)
    generated = Column(Numeric, nullable=True)
    is_forecast = Column(Boolean, default=False, primary_key=True)
    eoi_quantity = Column(Numeric, nullable=True)
    energy: Mapped[float] = mapped_column(Numeric, nullable=True)
    energy_quality_flag = Column(Numeric, nullable=False, default=0)

    __table_args__ = (
        Index("idx_facility_scada_facility_code_interval", "facility_code", "interval", postgresql_using="btree"),
        Index("idx_facility_scada_network_id", "network_id"),
        Index("idx_facility_scada_interval_facility_code", "interval", "facility_code"),
        Index("idx_facility_scada_is_forecast_interval", "is_forecast", "interval"),
        Index("idx_facility_scada_network_interval", "network_id", "interval", "is_forecast"),
        Index("idx_facility_scada_network_facility_interval", "network_id", "facility_code", "interval"),
        Index("facility_scada_new_interval_idx", "interval", unique=False, postgresql_ops={"interval": "DESC"}),
        Index("idx_facility_scada_interval_network", "interval", "network_id", postgresql_ops={"interval": "DESC"}),
    )

    def __str__(self) -> str:
        return f"<{self.__class__}: {self.trading_interval} {self.network_id} {self.facility_code}>"

    def __repr__(self) -> str:
        return f"{self.__class__}: {self.trading_interval} {self.network_id} {self.facility_code}"


class BalancingSummary(Base):
    __tablename__ = "balancing_summary"

    network_id = Column(Text, primary_key=True)
    interval: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), index=True, primary_key=True)
    network_region = Column(Text, primary_key=True)
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
    is_forecast = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_balancing_summary_network_id_interval", "network_id", "interval", postgresql_using="btree"),
        Index(
            "idx_balancing_summary_interval_network_region",
            "interval",
            "network_id",
            "network_region",
            postgresql_ops={"interval": "DESC"},
        ),
    )


class AEMOFacilityData(Base):
    __tablename__ = "aemo_facility_data"

    aemo_source = Column(Enum(AEMODataSource), primary_key=True)
    source_date = Column(Date, primary_key=True)
    name = Column(Text, nullable=True)
    name_network = Column(Text, nullable=True)
    network_region = Column(Text, primary_key=False)
    fueltech_id = Column(Text, nullable=True)
    status_id = Column(Text, nullable=True)
    duid = Column(Text, nullable=True)
    units_no = Column(Integer, nullable=True)
    capacity_registered = Column(Numeric, nullable=True)
    closure_year_expected = Column(Integer, nullable=True)


class AggregateFacilityDaily(Base):
    __tablename__ = "at_facility_daily"

    trading_day = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    network_id = Column(Text, primary_key=True, index=False, nullable=False)
    network_region = Column(Text, primary_key=True, nullable=False, index=False)
    facility_code = Column(Text, primary_key=True, index=True, nullable=False)
    fueltech_id = Column(Text, nullable=True)
    energy = Column(Numeric, nullable=True)
    market_value = Column(Numeric, nullable=True)
    emissions = Column(Numeric, nullable=True)

    __table_args__ = (
        Index("idx_at_facility_day_facility_code_trading_interval", "facility_code", "trading_day", postgresql_using="btree"),
        Index("idx_at_facility_daily_network_id_trading_interval", "network_id", "trading_day", postgresql_using="btree"),
        Index("idx_at_facility_daily_trading_interval_facility_code", "trading_day", "facility_code"),
        Index(
            "idx_at_facility_daily_facility_code_network_id_trading_day",
            "network_id",
            "facility_code",
            "trading_day",
            unique=True,
            postgresql_using="btree",
        ),
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


class AggregateNetworkFlowsV3(Base):
    __tablename__ = "at_network_flows_v3"

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
        Index("idx_at_network_flowsy_v3_network_id_trading_interval", "network_id", "trading_interval", postgresql_using="btree"),
        Index("idx_at_network_flows_v3_trading_interval_facility_code", "trading_interval", "network_id", "network_region"),
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

    record_id: Mapped[str] = Column(Text, primary_key=True, index=True)
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

    __table_args__ = (
        UniqueConstraint("record_id", "interval", name="excl_milestone_record_id_interval"),
        Index("idx_milestone_network_id", "network_id", postgresql_using="btree"),
        Index("idx_milestone_fueltech_id", "fueltech_id", postgresql_using="btree"),
    )
