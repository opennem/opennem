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
    Numeric,
    Sequence,
    String,
    Table,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

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


class FacilityStatus(Base, BaseModel):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class Participant(Base, BaseModel):
    __tablename__ = "participant"

    id = Column(
        Integer,
        Sequence("seq_participant_id", start=1000, increment=1),
        primary_key=True,
    )

    code = Column(Text, unique=True, index=True)
    name = Column(Text)
    network_name = Column(Text)
    network_code = Column(Text)
    country = Column(Text)
    abn = Column(Text)


class Revision(Base, BaseModel):

    __tablename__ = "revisions"

    id = Column(
        Integer,
        Sequence("seq_revision_id", start=1000, increment=1),
        primary_key=True,
    )

    schema = Column(Text, nullable=False, index=True)
    code = Column(Text, nullable=False, index=True)
    data = Column(JSON, nullable=True)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class Location(Base):
    __tablename__ = "location"

    id = Column(
        Integer, Sequence("seq_location_id", start=1000), primary_key=True
    )

    # station_id = Column(Integer, ForeignKey("station.id"))

    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)

    # Geo fields
    place_id = Column(Text, nullable=True, index=True)
    geocode_approved = Column(Boolean, default=False)
    geocode_skip = Column(Boolean, default=False)
    geocode_processed_at = Column(DateTime, nullable=True)
    geocode_by = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326))
    boundary = Column(Geometry("MULTIPOLYGON", srid=4326))


class Station(Base, BaseModel):
    __tablename__ = "station"

    def __str__(self):
        return "{} <{}>".format(self.name, self.code)

    def __repr__(self):
        return "{} {} <{}>".format(self.__class__, self.name, self.code)

    id = Column(
        Integer,
        Sequence("seq_station_id", start=1000, increment=1),
        primary_key=True,
    )

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
    location = relationship("Location")

    facilities = relationship("Facility")

    code = Column(Text, index=True, nullable=True)
    name = Column(Text)

    # Original network fields
    network_code = Column(Text, index=True)
    network_name = Column(Text)

    approved = Column(Boolean, default=False)
    approved_by = Column(Text)
    approved_at = Column(DateTime(timezone=True), nullable=True)

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

    @hybrid_property
    def lat(self) -> Optional[float]:
        if self.location.geom:
            return wkb.loads(bytes(self.location.geom.data)).y

        return None

    @hybrid_property
    def lng(self) -> Optional[float]:
        if self.location.geom:
            return wkb.loads(bytes(self.location.geom.data)).x

        return None


class Facility(Base, BaseModel):
    __tablename__ = "facility"

    def __str__(self):
        return "{} <{}>".format(self.code, self.fueltech_id)

    def __repr__(self):
        return "{} {} <{}>".format(self.__class__, self.code, self.fueltech_id)

    id = Column(
        Integer,
        Sequence("seq_facility_id", start=1000, increment=1),
        primary_key=True,
    )

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
    fueltech = relationship("FuelTech", back_populates="facilities")

    status_id = Column(
        Text,
        ForeignKey("facility_status.code", name="fk_facility_status_code"),
    )
    status = relationship("FacilityStatus")

    station_id = Column(
        Integer,
        ForeignKey("station.id", name="fk_station_status_code"),
        nullable=True,
    )
    station = relationship("Station", back_populates="facilities")

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


class FacilityScada(Base, BaseModel):
    """
        Facility Scada
    """

    __tablename__ = "facility_scada"

    trading_interval = Column(DateTime, index=True, primary_key=True)

    facility_id = Column(
        Integer,
        ForeignKey("facility.id", name="fk_facility_scada_facility_id"),
        primary_key=True,
    )
    facility = relationship("Facility")

    generated = Column(Numeric, nullable=True)
    eoi_quantity = Column(Numeric, nullable=True)


class BalancingSummary(Base, BaseModel):

    __tablename__ = "balancing_summary"

    network_id = Column(
        Text,
        ForeignKey("network.code", name="fk_balancing_summary_network_code"),
    )
    network = relationship("Network")

    trading_interval = Column(DateTime, index=True, primary_key=True)
    forecast_load = Column(Numeric, nullable=True)
    generation_scheduled = Column(Numeric, nullable=True)
    generation_non_scheduled = Column(Numeric, nullable=True)
    generation_total = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
