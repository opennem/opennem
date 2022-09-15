"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

import enum
from decimal import Decimal
from typing import List, Optional

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
    LargeBinary,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from opennem.core.dispatch_type import DispatchType
from opennem.core.oid import get_ocode, get_oid
from opennem.utils.sql import time_bucket
from opennem.workers.facility_data_ranges import FacilitySeenRange

Base = declarative_base()
metadata = Base.metadata


class BaseModel(object):
    """
    Base model for both NEM and WEM

    """

    created_by = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
    )

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
    """Metadata about crawlers where k,v can be stored"""

    __tablename__ = "crawl_meta"

    spider_name = Column(Text, nullable=False, primary_key=True)
    data = Column(MutableDict.as_mutable(JSONB), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CrawlerSource(enum.Enum):
    nemweb = "nemweb"
    wem = "wem"


class CrawlHistory(Base):
    """updated crawl meta that tracks invidual intervals"""

    __tablename__ = "crawl_history"

    source = Column(Enum(CrawlerSource), nullable=False, primary_key=True, default=CrawlerSource.nemweb)
    crawler_name = Column(Text, nullable=False, primary_key=True)

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_crawl_info_network_code"),
        primary_key=True,
        nullable=False,
    )
    network = relationship("Network", lazy="joined")

    interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)
    inserted_records = Column(Integer, nullable=True)

    crawled_time = Column(DateTime(timezone=True), server_default=func.now())
    processed_time = Column(DateTime(timezone=True), server_default=func.now())


class FuelTech(Base, BaseModel):
    __tablename__ = "fueltech"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    renewable = Column(Boolean, default=False)

    facilities = relationship("Facility")


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

    # data start and end dates cached here
    data_start_date = Column(TIMESTAMP(timezone=True), index=True, nullable=True)
    data_end_date = Column(TIMESTAMP(timezone=True), index=True, nullable=True)

    # Network that is used to price this network
    network_price = Column(Text, nullable=False)

    # This stores the shift in time for the network
    # trading intervals
    interval_shift = Column(Integer, nullable=False, default=0)

    # record is exported
    export_set = Column(Boolean, default=True, nullable=False)

    regions = relationship("NetworkRegion")


class NetworkRegion(Base, BaseModel):
    __tablename__ = "network_region"

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_network_region_network_code"),
        primary_key=True,
        nullable=False,
    )
    network = relationship("Network", back_populates="regions")

    code = Column(Text, primary_key=True)
    timezone = Column(Text, nullable=True)
    timezone_database = Column(Text, nullable=True)
    offset = Column(Integer, nullable=True)

    # record is exported
    export_set = Column(Boolean, default=True, nullable=False)


class FacilityStatus(Base, BaseModel):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class Participant(Base, BaseModel):
    __tablename__ = "participant"

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
    )

    code = Column(Text, unique=True, index=True)
    name = Column(Text)
    network_name = Column(Text)
    network_code = Column(Text)
    country = Column(Text)
    abn = Column(Text)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class Photo(Base):
    __tablename__ = "photo"

    hash_id = Column(Text, nullable=False, primary_key=True, index=True)

    station_id = Column(
        Integer,
        ForeignKey("station.id", name="fk_photos_station_id"),
        nullable=True,
    )
    station = relationship("Station", back_populates="photos")

    name = Column(Text)
    mime_type = Column(Text)
    original_url = Column(Text, nullable=True)
    data = Column(LargeBinary, nullable=True)
    width = Column(Integer)
    height = Column(Integer)

    license_type = Column(Text, nullable=True)
    license_link = Column(Text, nullable=True)
    author = Column(Text, nullable=True)
    author_link = Column(Text, nullable=True)

    processed = Column(Boolean, default=False)
    processed_by = Column(Text)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=1)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def photo_url(self) -> Optional[str]:
        if self.name:
            return "https://photos.opennem.org.au/{}".format(self.name)

        return None


class BomStation(Base):
    __tablename__ = "bom_station"

    __table_args__ = (Index("idx_bom_station_geom", "geom", postgresql_using="gist"),)

    code = Column(Text, primary_key=True)
    state = Column(Text)
    name = Column(Text)
    web_code = Column(Text, nullable=True)
    name_alias = Column(Text, nullable=True)
    registered = Column(Date)

    # priority from 1-5
    priority = Column(Integer, default=5)
    is_capital = Column(Boolean, default=False)

    website_url = Column(Text, nullable=True)
    feed_url = Column(Text, nullable=True)

    altitude = Column(Integer, nullable=True)

    geom = Column(Geometry("POINT", srid=4326, spatial_index=False))

    @hybrid_property
    def lat(self) -> Optional[float]:
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).y

        return None

    @hybrid_property
    def lng(self) -> Optional[float]:
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).x

        return None


class BomObservation(Base):
    __tablename__ = "bom_observation"

    observation_time = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)

    station_id = Column(
        Text,
        ForeignKey("bom_station.code", name="fk_bom_observation_station_code"),
        primary_key=True,
    )
    station = relationship("BomStation")

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


class Location(Base):
    __tablename__ = "location"

    __table_args__ = (
        Index("idx_location_geom", "geom", postgresql_using="gist"),
        Index("idx_location_boundary", "boundary", postgresql_using="gist"),
    )

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)

    # station_id = Column(Integer, ForeignKey("station.id"))

    # @TODO sort out this join based on this lateral query ..
    # @NOTE this might not be the best way to do this as
    # the closest weather station is not always the most relevant

    #  select
    #       l.id,
    #       l.locality,
    #       l.state,
    #       closest_station.state,
    #       closest_station.code,
    #       closest_station.dist
    #  from location l
    #  left join lateral (
    # 	select
    #       code, state, ST_Distance(l.geom, bom_station.geom) / 1000 as dist
    #   from bom_station order by l.geom <-> bom_station.geom limit 1
    #  ) AS closest_station on TRUE;

    # weather_station = relationship(
    #     "BomStation",
    #     primaryjoin=\
    #       "func.ST_ClosestPoint(remote(BomStation.geom), \
    #       foreign(Location.geom))",
    #     viewonly=True,
    #     uselist=True,
    #     lazy="joined",
    # )

    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)

    # an OSM way id such as 395531577
    osm_way_id = Column(Text, nullable=True)

    # Geo fields
    place_id = Column(Text, nullable=True, index=True)
    geocode_approved = Column(Boolean, default=False)
    geocode_skip = Column(Boolean, default=False)
    geocode_processed_at = Column(DateTime, nullable=True)
    geocode_by = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326, spatial_index=False))
    boundary = Column(Geometry("POLYGON", srid=4326, spatial_index=True))

    @hybrid_property
    def lat(self) -> Optional[float]:
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).y

        return None

    @hybrid_property
    def lng(self) -> Optional[float]:
        if self.geom:
            return wkb.loads(bytes(self.geom.data)).x

        return None


class Station(Base, BaseModel):
    __tablename__ = "station"

    __table_args__ = (UniqueConstraint("code", name="excl_station_network_duid"),)

    def __str__(self) -> str:
        return "{} <{}>".format(self.name, self.code)

    def __repr__(self) -> str:
        return "{} {} <{}>".format(self.__class__, self.name, self.code)

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
    )

    participant_id = Column(
        Integer,
        ForeignKey("participant.id", name="fk_station_participant_id"),
        nullable=True,
    )
    participant = relationship(
        "Participant",
        cascade="all, delete",
    )

    location_id = Column(
        Integer,
        ForeignKey("location.id", name="fk_station_location_id"),
        nullable=True,
    )
    location = relationship(
        "Location",
        lazy="joined",
        innerjoin=False,
        cascade="all, delete",
    )

    facilities = relationship(
        "Facility",
        lazy="joined",
        innerjoin=False,
        cascade="all, delete",
    )

    photos = relationship(
        "Photo",
        lazy="joined",
        innerjoin=False,
        cascade="all, delete",
    )

    code = Column(Text, index=True, nullable=False, unique=True)
    name = Column(Text)

    # wikipedia links
    description = Column(Text, nullable=True)
    wikipedia_link = Column(Text, nullable=True)
    wikidata_id = Column(Text, nullable=True)

    # Original network fields
    network_code = Column(Text, index=True)
    network_name = Column(Text)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Website
    website_url = Column(Text, nullable=True)

    @hybrid_property
    def facility_codes(self) -> List[str]:
        """Returns a list of facility codes for this station

        Returns:
            List[str]: facility codes
        """

        _fac_codes = list(set([f.code for f in self.facilities]))

        return _fac_codes

    @hybrid_property
    def scada_range(self) -> Optional[FacilitySeenRange]:
        """[summary]

        Returns:
            FacilitySeenRange: [description]
        """
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
    def capacity_registered(self) -> Optional[float]:
        """
        This is the sum of registered capacities for all units for
        this station

        """
        cap_reg: Optional[float] = None

        for fac in self.facilities:  # pylint: disable=no-member
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

    @hybrid_property
    def oid(self) -> str:
        return get_oid(self)

    @hybrid_property
    def ocode(self) -> str:
        return get_ocode(self)


class Facility(Base, BaseModel):
    __tablename__ = "facility"

    __table_args__ = (UniqueConstraint("network_id", "code", name="excl_facility_network_id_code"),)

    def __str__(self) -> str:
        return "{} <{}>".format(self.code, self.fueltech_id)

    def __repr__(self) -> str:
        return "{} {} <{}>".format(self.__class__, self.code, self.fueltech_id)

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
    )

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_station_network_code"),
        nullable=False,
    )
    network = relationship("Network", lazy="joined", innerjoin=True)

    fueltech_id = Column(
        Text,
        ForeignKey("fueltech.code", name="fk_facility_fueltech_id"),
        nullable=True,
    )
    fueltech = relationship("FuelTech", back_populates="facilities", lazy="joined", innerjoin=False)

    status_id = Column(
        Text,
        ForeignKey("facility_status.code", name="fk_facility_status_code"),
    )
    status = relationship("FacilityStatus", lazy="joined", innerjoin=True)

    station_id = Column(
        Integer,
        ForeignKey("station.id", name="fk_facility_station_code"),
        nullable=True,
    )
    # station = relationship("Station", back_populates="facilities")

    # DUID but modified by opennem as an identifier
    code = Column(Text, index=True, nullable=False, unique=True)

    # Network details
    network_code = Column(Text, nullable=True, index=True)
    network_region = Column(Text, index=True)
    network_name = Column(Text)

    active = Column(Boolean, default=True)

    dispatch_type = Column(Enum(DispatchType), nullable=False, default=DispatchType.GENERATOR)

    # @TODO remove when ref count is 0
    capacity_registered = Column(Numeric, nullable=True)

    registered = Column(DateTime, nullable=True)
    deregistered = Column(DateTime, nullable=True)
    expected_closure_date = Column(DateTime, nullable=True)
    expected_closure_year = Column(Integer, nullable=True)

    unit_id = Column(Integer, nullable=True)
    unit_number = Column(Integer, nullable=True)
    unit_alias = Column(Text, nullable=True)
    unit_capacity = Column(Numeric, nullable=True)

    # t CO2-e /MWh
    emissions_factor_co2 = Column(Numeric, nullable=True)

    # interconnector metadata
    interconnector = Column(Boolean, default=False, index=True)
    interconnector_region_to = Column(Text, nullable=True, index=True)
    interconnector_region_from = Column(Text, nullable=True, index=True)

    # first seen / last seen in scada data
    data_first_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    data_last_seen = Column(DateTime(timezone=True), nullable=True, index=True)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def capacity_aggregate(self) -> Optional[float]:
        """
        This is unit_no * unit_capacity and can differ from registered

        """
        num_units = 1
        cap_aggr = None

        if not self.active:
            return 0

        if self.unit_number and type(self.unit_number) is int:
            num_units = self.unit_number

        if self.unit_capacity and type(self.unit_capacity) is Decimal:
            cap_aggr = num_units * self.unit_capacity

        if cap_aggr and type(cap_aggr) is Decimal:
            cap_aggr = round(cap_aggr, 2)

        return cap_aggr

    @hybrid_property
    def status_label(self) -> Optional[str]:
        return self.status.label if self.status else None

    @hybrid_property
    def fueltech_label(self) -> Optional[str]:
        return self.fueltech.label if self.fueltech else None

    @hybrid_property
    def oid(self) -> str:
        return get_oid(self)

    @hybrid_property
    def ocode(self) -> str:
        return get_ocode(self)


class FacilityScada(Base, BaseModel):
    """
    Facility Scada
    """

    __tablename__ = "facility_scada"

    def __str__(self) -> str:
        return "<{}: {} {} {}>".format(
            self.__class__,
            self.trading_interval,
            self.network_id,
            self.facility_code,
        )

    def __repr__(self) -> str:
        return "{}: {} {} {}".format(
            self.__class__,
            self.trading_interval,
            self.network_id,
            self.facility_code,
        )

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_balancing_summary_network_code"),
        primary_key=True,
        nullable=False,
    )
    network = relationship("Network")

    trading_interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)

    facility_code = Column(Text, nullable=False, primary_key=True, index=True)

    # MW
    generated = Column(Numeric, nullable=True)

    is_forecast = Column(Boolean, default=False, primary_key=True)

    # MWh
    eoi_quantity = Column(Numeric, nullable=True)

    energy_quality_flag = Column(Numeric, nullable=False, default=0)

    __table_args__ = (
        Index(
            "idx_facility_scada_facility_code_trading_interval",
            facility_code,
            trading_interval.desc(),
        ),
        Index("idx_facility_scada_network_id", network_id),
        Index("idx_facility_scada_network_id_trading_interval", network_id, trading_interval.desc()),
        Index("idx_facility_scada_trading_interval_facility_code", trading_interval, facility_code),
        # This index is used by aggregate tables
        Index(
            "idx_facility_scada_trading_interval_desc_facility_code",
            time_bucket("'00:30:00'::interval", trading_interval).desc(),
            facility_code,
        ),
    )


class BalancingSummary(Base, BaseModel):

    __tablename__ = "balancing_summary"

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_balancing_summary_network_code"),
        primary_key=True,
    )
    network = relationship("Network")

    trading_interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True)
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
        Index(
            "idx_balancing_summary_network_id_trading_interval",
            network_id,
            trading_interval.desc(),
        ),
        Index(
            "idx_balancing_summary_network_region_trading_interval",
            network_region,
            trading_interval.desc(),
        ),
    )


# Aggregate tables


class AggregateFacilityDaily(Base):
    """
    Facility Dailies Aggregates
    """

    __tablename__ = "at_facility_daily"

    # def __str__(self) -> str:
    #     return "<{}: {} {} {}>".format(
    #         self.__class__,
    #         self.trading_interval,
    #         self.network_id,
    #         self.facility_code,
    #     )

    # def __repr__(self) -> str:
    #     return "{}: {} {} {}".format(
    #         self.__class__,
    #         self.trading_interval,
    #         self.network_id,
    #         self.facility_code,
    #     )

    trading_day = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_at_facility_daily_network_code"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    network = relationship("Network")

    facility_code = Column(
        Text,
        ForeignKey("facility.code", name="fk_at_facility_daily_facility_code"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    facility = relationship("Facility")

    fueltech_id = Column(Text, nullable=True)

    # MWh
    energy = Column(Numeric, nullable=True)

    market_value = Column(Numeric, nullable=True)

    # tCO2-e
    emissions = Column(Numeric, nullable=True)

    __table_args__ = (
        Index(
            "idx_at_facility_day_facility_code_trading_interval",
            facility_code,
            trading_day.desc(),
        ),
        Index("idx_at_facility_daily_network_id_trading_interval", network_id, trading_day.desc()),
        Index("idx_at_facility_daily_trading_interval_facility_code", trading_day, facility_code),
    )


class AggregateNetworkFlows(Base, BaseModel):
    """
    Network Flows Aggregate Table
    """

    __tablename__ = "at_network_flows"

    trading_interval = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_at_network_flows_network_code"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    network = relationship("Network")

    network_region = Column(Text, index=True, primary_key=True, nullable=False)

    # GWh
    energy_imports = Column(Numeric, nullable=True)
    energy_exports = Column(Numeric, nullable=True)

    market_value_imports = Column(Numeric, nullable=True)
    market_value_exports = Column(Numeric, nullable=True)

    # tCO2-e
    emissions_imports = Column(Numeric, nullable=True)
    emissions_exports = Column(Numeric, nullable=True)

    __table_args__ = (
        Index(
            "idx_at_network_flowsy_network_id_trading_interval",
            network_id,
            trading_interval.desc(),
        ),
        Index(
            "idx_at_network_flows_trading_interval_facility_code",
            trading_interval,
            network_id,
            network_region,
        ),
    )


class AggregateNetworkDemand(Base):
    """
    Network demand aggregates for energy and price
    """

    __tablename__ = "at_network_demand"

    trading_day = Column(TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False)

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_at_facility_daily_network_code"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    network = relationship("Network")

    network_region = Column(Text, primary_key=True)

    demand_energy = Column(Numeric, nullable=True)
    demand_market_value = Column(Numeric, nullable=True)

    __table_args__ = (
        Index("idx_at_network_demand_network_id_trading_interval", network_id, trading_day.desc()),
        Index("idx_at_network_demand_trading_interval_network_region", trading_day, network_id, network_region),
    )
