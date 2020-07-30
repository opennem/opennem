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
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from opennem.core.oid import get_ocode, get_oid

Base = declarative_base()
metadata = Base.metadata


class BaseModel(object):
    """
        Base model for both NEM and WEM

        Each table has an overrid for update and additional meta fields

        @TODO - upsert support for postgresql and mysql dialects (see db/__init__)
    """

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key == "id" or key.endswith("_id"):
                continue

            # @TODO watch how we do updates so we don't overwrite data
            cur_val = getattr(self, key)
            if key not in [None, ""]:
                setattr(self, key, value)

    def __compile_query(self, query):
        """Via http://nicolascadou.com/blog/2014/01/printing-actual-sqlalchemy-queries"""
        compiler = (
            query.compile
            if not hasattr(query, "statement")
            else query.statement.compile
        )
        return compiler(dialect=postgresql.dialect())

    def __upsert(
        self,
        session,
        model,
        rows,
        as_of_date_col="report_date",
        no_update_cols=[],
    ):
        table = model.__table__

        stmt = self.insert(table).values(rows)

        update_cols = [
            c.name
            for c in table.c
            if c not in list(table.primary_key.columns)
            and c.name not in no_update_cols
        ]

        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=table.primary_key.columns,
            set_={k: getattr(stmt.excluded, k) for k in update_cols},
            index_where=(model.report_date < stmt.excluded.report_date),
        )

        print(self.compile_query(on_conflict_stmt))
        session.execute(on_conflict_stmt)

    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FuelTech(Base, BaseModel):
    __tablename__ = "fueltech"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=True)
    renewable = Column(Boolean, default=False)


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
    country = Column(Text)
    abn = Column(Text)


class Station(Base, BaseModel):
    __tablename__ = "station"

    id = Column(
        Integer,
        Sequence("seq_station_id", start=1000, increment=1),
        primary_key=True,
    )

    network_id = Column(
        Text, ForeignKey("network.code", name="fk_station_network_code"),
    )
    network = relationship("Network")

    participant_id = Column(
        Integer,
        ForeignKey("participant.id", name="fk_station_participant_id"),
        nullable=True,
    )
    participant = relationship("Participant")

    facilities = relationship("Facility")

    code = Column(Text, unique=True, index=True, nullable=True)
    name = Column(Text)

    address1 = Column(Text)
    address2 = Column(Text)
    locality = Column(Text)
    state = Column(Text)
    postcode = Column(Text, nullable=True)

    # Original network fields
    network_code = Column(Text, index=True)
    network_name = Column(Text)
    network_region = Column(Text)

    # Capacity fields
    capacity_registered = Column(Numeric, nullable=True)

    # Geo fields
    place_id = Column(Text, nullable=True, index=True)
    geocode_approved = Column(Boolean, default=False)
    geocode_skip = Column(Boolean, default=False)
    geocode_processed_at = Column(DateTime, nullable=True)
    geocode_by = Column(Text, nullable=True)
    geom = Column(Geometry("POINT", srid=4326))
    boundary = Column(Geometry("MULTIPOLYGON", srid=4326))

    @hybrid_property
    def oid(self):
        return get_oid(self)

    @hybrid_property
    def ocode(self):
        return get_ocode(self)


class Facility(Base, BaseModel):
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
    station = relationship("Station", back_populates="facilities")

    # DUID but modified by opennem as an identifier
    code = Column(Text, nullable=True, index=True, unique=True)

    # Network details
    network_code = Column(Text, nullable=True, index=True)
    network_region = Column(Text, index=True)
    network_name = Column(Text)

    active = Column(Boolean, default=True)

    # @TODO remove when ref count is 0
    capacity_registered = Column(Numeric, nullable=True)

    registered = Column(DateTime)

    unit_id = Column(Numeric, nullable=True)
    unit_number = Column(Numeric, nullable=True)
    unit_alias = Column(Text, nullable=True)
    unit_capacity = Column(Numeric, nullable=True)
    # unit_number_max = Column(Numeric, nullable=True)

    @hybrid_property
    def oid(self):
        return get_oid(self)

    @hybrid_property
    def ocode(self):
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

    trading_interval = Column(DateTime, index=True, primary_key=True)
    forecast_load = Column(Numeric, nullable=True)
    generation_scheduled = Column(Numeric, nullable=True)
    generation_non_scheduled = Column(Numeric, nullable=True)
    generation_total = Column(Numeric, nullable=True)
    price = Column(Numeric, nullable=True)
