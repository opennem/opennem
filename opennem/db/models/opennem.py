"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Sequence,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class FuelTech(Base, NemModel):
    __tablename__ = "fueltech"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    renewable = Column(Boolean, default=False)


class Network(Base, NemModel):
    __tablename__ = "network"

    code = Column(Text, primary_key=True)
    country = Column(Text, nullable=False)
    label = Column(Text, nullable=True)


class FacilityStatus(Base):
    __tablename__ = "facility_status"

    code = Column(Text, primary_key=True)
    label = Column(Text)


class Participant(Base, NemModel):
    __tablename__ = "participant"

    id = Column(
        Integer,
        Sequence("seq_participant_id", start=1000, increment=1),
        primary_key=True,
    )

    code = Column(Text, unique=True, index=True)
    name = Column(Text)
    network_name = Column(Text)
    country = Column(Text)
    abn = Column(Text)


class Station(Base, NemModel):
    __tablename__ = "station"

    id = Column(
        Integer,
        Sequence("seq_station_id", start=1000, increment=1),
        primary_key=True,
    )

    network_id = Column(
        Integer, ForeignKey("network.id", name="fk_station_network_id"),
    )
    network = relationship("Network")

    participant_id = Column(
        Integer,
        ForeignKey("participant.id", name="fk_station_participant_id"),
        nullable=True,
    )
    participant = relationship("Participant")

    code = Column(Text, unique=True, index=True, nullable=True)
    name = Column(Text)

    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)

    # Original network fields
    network_code = Column(Text)
    network_name = Column(Text)
    network_region = Column(Text)

    # Capacity fields
    capacity_nameplate = Column(Numeric, nullable=True)
    capacity_registered = Column(Numeric, nullable=True)

    # Geo fields
    place_id = Column(Text, nullable=True, index=True)
    geom = Column(Geometry("POINT", srid=4326))
    boundary = Column(Geometry("MULTIPOLYGON", srid=4326))


class Facility(Base, NemModel):
    __tablename__ = "facility"

    id = Column(
        Integer,
        Sequence("seq_facility_id", start=1000, increment=1),
        primary_key=True,
    )

    participant_id = Column(
        Integer,
        ForeignKey("participant.id", name="fk_facility_participant_id"),
        nullable=True,
    )
    participant = relationship("Participant")

    fueltech_id = Column(
        Text,
        ForeignKey("fueltech.code", name="fk_facility_fueltech_id"),
        nullable=True,
    )
    fueltech = relationship(
        "FuelTech", backref=backref("nem_facilities", cascade="all,delete")
    )

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
    station = relationship("Station")

    name = Column(Text)
    name_clean = Column(Text)

    # DUID
    code = Column(Text, nullable=True, index=True)
    region = Column(Text, index=True)

    active = Column(Boolean, default=True)

    # @TODO remove when ref count is 0
    capacity_nameplate = Column(Numeric, nullable=True)
    capacity_registered = Column(Numeric, nullable=True)
    capacity_maximum = Column(Numeric, nullable=True)
    capacity_minimum = Column(Numeric, nullable=True)

    registered = Column(DateTime)

    unit_size = Column(Numeric, nullable=True)
    unit_number = Column(Text, nullable=True)


class FacilityScada(Base, NemModel):
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


class BalancingSummary(Base, NemModel):

    __tablename__ = "balancing_summary"

    trading_interval = Column(DateTime, index=True, primary_key=True)
    forecast_load = Column(Numeric, nullable=True)
    generation_scheduled = Column(Numeric, nullable=True)
    generation_non_scheduled = Column(Numeric, nullable=True)
    generation_total = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
