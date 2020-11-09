"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

from decimal import Decimal
from typing import Optional

from dictalchemy import DictableModel
from geoalchemy2 import Geometry
from shapely import wkb
from sqlalchemy import (
    JSON,
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
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from opennem.core.dispatch_type import DispatchType
from opennem.core.oid import get_ocode, get_oid

Base = declarative_base(cls=DictableModel)
metadata = Base.metadata


class BaseModel(object):
    """
        Base model for both NEM and WEM

    """

    created_by = Column(Text, nullable=True)
    # updated_by = Column(Text, nullable=True)
    # processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FuelTech(Base, BaseModel):
    __tablename__ = "fueltech"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    renewable = Column(Boolean, default=False)

    facilities = relationship("Facility")


class Network(Base, BaseModel):
    __tablename__ = "network"

    code = Column(Text, primary_key=True)
    country = Column(Text, nullable=False)
    label = Column(Text, nullable=True)
    timezone = Column(Text, nullable=False)
    timezone_database = Column(Text, nullable=True)
    offset = Column(Integer, nullable=True)
    interval_size = Column(Integer, nullable=False)

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


class FacilityStatus(Base, BaseModel):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class Participant(Base, BaseModel):
    __tablename__ = "participant"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True,)

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

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)

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

    __table_args__ = (
        Index("idx_bom_station_geom", "geom", postgresql_using="gist"),
    )

    code = Column(Text, primary_key=True)
    state = Column(Text)
    name = Column(Text)
    name_alias = Column(Text, nullable=True)
    registered = Column(Date)

    # priority from 1-5
    priority = Column(Integer, default=5)
    is_capital = Column(Boolean, default=False)

    website_url = Column(Text, nullable=True)
    feed_url = Column(Text, nullable=True)

    observations = relationship("BomObservation")
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

    observation_time = Column(
        TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False
    )

    station_id = Column(
        Text,
        ForeignKey("bom_station.code", name="fk_bom_observation_station_code"),
        primary_key=True,
    )
    station = relationship("BomStation")
    temp_apparent = Column(Numeric)
    temp_air = Column(Numeric)
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

    #  select l.id, l.locality, l.state, closest_station.state, closest_station.code, closest_station.dist from location l
    #  left join lateral (
    # 	select code, state, ST_Distance(l.geom, bom_station.geom) / 1000 as dist from bom_station order by l.geom <-> bom_station.geom limit 1
    #  ) AS closest_station on TRUE;

    # weather_station = relationship(
    #     "BomStation",
    #     primaryjoin="func.ST_ClosestPoint(remote(BomStation.geom), foreign(Location.geom))",
    #     viewonly=True,
    #     uselist=True,
    #     lazy="joined",
    # )

    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)

    revisions = relationship("Revision", lazy="joined")

    # Geo fields
    place_id = Column(Text, nullable=True, index=True)
    geocode_approved = Column(Boolean, default=False)
    geocode_skip = Column(Boolean, default=False)
    geocode_processed_at = Column(DateTime, nullable=True)
    geocode_by = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326, spatial_index=False))
    boundary = Column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False))

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

    # __table_args__ = (
    #     UniqueConstraint(
    #         "customer_id", "location_code", name="_customer_location_uc"
    #     ),
    # )

    def __str__(self):
        return "{} <{}>".format(self.name, self.code)

    def __repr__(self):
        return "{} {} <{}>".format(self.__class__, self.name, self.code)

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True,)

    participant_id = Column(
        Integer,
        ForeignKey("participant.id", name="fk_station_participant_id"),
        nullable=True,
    )
    participant = relationship("Participant")

    location_id = Column(
        Integer,
        ForeignKey("location.id", name="fk_station_location_id"),
        nullable=True,
    )
    location = relationship("Location", lazy="joined", innerjoin=True)

    facilities = relationship("Facility", lazy="joined", innerjoin=True)

    revisions = relationship("Revision")

    photos = relationship("Photo")

    code = Column(Text, index=True, nullable=True)
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

    @hybrid_property
    def network(self) -> Optional[Network]:
        """
            Return the network from the facility

        """
        if not self.facilities or not len(self.facilities) > 0:
            return None

        return self.facilities[0].network

    @hybrid_property
    def capacity_registered(self) -> Optional[int]:
        """
            This is the sum of registered capacities for all units for
            this station

        """
        cap_reg = None

        for fac in self.facilities:
            if (
                fac.capacity_registered
                and type(fac.capacity_registered) in [int, float, Decimal]
                and fac.status_id
                in ["operating", "committed", "commissioning"]
                and fac.dispatch_type == DispatchType.GENERATOR
                and fac.active
            ):
                if not cap_reg:
                    cap_reg = 0

                cap_reg += fac.capacity_registered

        if cap_reg:
            cap_reg = round(cap_reg, 2)

        return cap_reg

    @hybrid_property
    def capacity_aggregate(self) -> Optional[int]:
        """
            This is the sum of aggregate capacities for all units

        """
        cap_agg = None

        for fac in self.facilities:
            if (
                fac.capacity_aggregate
                and type(fac.capacity_aggregate) in [int, float, Decimal]
                and fac.status_id
                in ["operating", "committed", "commissioning"]
                and fac.dispatch_type == DispatchType.GENERATOR
                and fac.active
            ):
                if not cap_agg:
                    cap_agg = 0

                cap_agg += fac.capacity_aggregate

        if cap_agg:
            cap_agg = round(cap_agg, 2)

        return cap_agg

    @hybrid_property
    def oid(self) -> str:
        return get_oid(self)

    @hybrid_property
    def ocode(self) -> str:
        return get_ocode(self)


class Facility(Base, BaseModel):
    __tablename__ = "facility"

    def __str__(self):
        return "{} <{}>".format(self.code, self.fueltech_id)

    def __repr__(self):
        return "{} {} <{}>".format(self.__class__, self.code, self.fueltech_id)

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True,)

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_station_network_code"),
        nullable=False,
    )
    network = relationship("Network")

    fueltech_id = Column(
        Text,
        ForeignKey("fueltech.code", name="fk_facility_fueltech_id"),
        nullable=True,
    )
    fueltech = relationship(
        "FuelTech", back_populates="facilities", lazy="joined", innerjoin=True
    )

    status_id = Column(
        Text,
        ForeignKey("facility_status.code", name="fk_facility_status_code"),
    )
    status = relationship("FacilityStatus", lazy="joined", innerjoin=True)

    station_id = Column(
        Integer,
        ForeignKey("station.id", name="fk_station_status_code"),
        nullable=True,
    )
    # station = relationship("Station", back_populates="facilities")

    revisions = relationship("Revision")

    # DUID but modified by opennem as an identifier
    code = Column(Text, index=True)

    # Network details
    network_code = Column(Text, nullable=True, index=True)
    network_region = Column(Text, index=True)
    network_name = Column(Text)

    active = Column(Boolean, default=True)

    dispatch_type = Column(
        Enum(DispatchType), nullable=False, default=DispatchType.GENERATOR
    )

    # @TODO remove when ref count is 0
    capacity_registered = Column(Numeric, nullable=True)

    registered = Column(DateTime, nullable=True)
    deregistered = Column(DateTime, nullable=True)

    unit_id = Column(Integer, nullable=True)
    unit_number = Column(Integer, nullable=True)
    unit_alias = Column(Text, nullable=True)
    unit_capacity = Column(Numeric, nullable=True)
    # unit_number_max = Column(Numeric, nullable=True)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def capacity_aggregate(self) -> Optional[int]:
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

        if type(cap_aggr) is Decimal:
            cap_aggr = round(cap_aggr, 2)

        return cap_aggr

    @hybrid_property
    def duid(self) -> str:
        return self.network_code or self.code

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


class Revision(Base, BaseModel):

    __tablename__ = "revisions"

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True,)

    station_id = Column(
        Integer,
        ForeignKey("station.id", name="fk_revision_station_id"),
        nullable=True,
    )
    station = relationship(
        "Station", back_populates="revisions", lazy="joined"
    )

    facility_id = Column(
        Integer,
        ForeignKey("facility.id", name="fk_revision_facility_id"),
        nullable=True,
    )
    facility = relationship(
        "Facility", back_populates="revisions", lazy="joined"
    )

    location_id = Column(
        Integer,
        ForeignKey("location.id", name="fk_revision_location_id"),
        nullable=True,
    )
    location = relationship(
        "Location", back_populates="revisions", lazy="joined"
    )

    changes = Column(JSON, nullable=True)
    previous = Column(JSON, nullable=True)

    is_update = Column(Boolean, default=False)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_comment = Column(Text, nullable=True)

    discarded = Column(Boolean, default=False)
    discarded_by = Column(Text)
    discarded_at = Column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def parent_id(self) -> str:
        return self.station_id or self.facility_id or self.location_id

    @hybrid_property
    def parent_type(self) -> str:
        if self.station_id:
            return "station"

        if self.facility_id:
            return "facility"

        if self.location_id:
            return "location"

        return ""

    @hybrid_property
    def station_owner_id(self) -> int:
        if self.station_id:
            return self.station_id

        if self.facility_id:
            return self.facility.station.id

        if self.location:
            return self.location.station.id

    @hybrid_property
    def station_owner_name(self) -> str:
        if self.station_id:
            return self.station.name

        if self.facility_id:
            return self.facility.station.name

        if self.location:
            return self.location.station.name

    @hybrid_property
    def station_owner_code(self) -> str:
        if self.station_id:
            return self.station.code

        if self.facility_id:
            return self.facility.station.code

        if self.location:
            return self.location.station.code


class FacilityScada(Base, BaseModel):
    """
        Facility Scada
    """

    __tablename__ = "facility_scada"

    __table_args__ = (
        Index(
            "idx_facility_scada_trading_interval_year",
            text("date_trunc('year', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_facility_scada_trading_interval_month",
            text("date_trunc('month', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_facility_scada_trading_interval_day",
            text("date_trunc('day', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_facility_scada_trading_interval_hour",
            text("date_trunc('hour', trading_interval AT TIME ZONE 'UTC')"),
        ),
        # new timezone based indicies
        # @NOTE: other indicies in migration files
    )

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

    trading_interval = Column(
        TIMESTAMP(timezone=True), index=True, primary_key=True, nullable=False
    )

    facility_code = Column(Text, nullable=False, primary_key=True, index=True)
    generated = Column(Numeric, nullable=True)
    is_forecast = Column(Boolean, default=False)
    eoi_quantity = Column(Numeric, nullable=True)


class BalancingSummary(Base, BaseModel):

    __tablename__ = "balancing_summary"

    __table_args__ = (
        Index(
            "idx_balancing_summary_trading_interval_year",
            text("date_trunc('year', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_balancing_summary_trading_interval_month",
            text("date_trunc('month', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_balancing_summary_trading_interval_day",
            text("date_trunc('day', trading_interval AT TIME ZONE 'UTC')"),
        ),
        Index(
            "idx_balancing_summary_trading_interval_hour",
            text("date_trunc('hour', trading_interval AT TIME ZONE 'UTC')"),
        ),
    )

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_balancing_summary_network_code"),
        primary_key=True,
    )
    network = relationship("Network")

    trading_interval = Column(
        TIMESTAMP(timezone=True), index=True, primary_key=True
    )
    network_region = Column(Text, primary_key=True)
    forecast_load = Column(Numeric, nullable=True)
    generation_scheduled = Column(Numeric, nullable=True)
    generation_non_scheduled = Column(Numeric, nullable=True)
    generation_total = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
    is_forecast = Column(Boolean, default=False)

