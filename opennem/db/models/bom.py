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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class BomStation(Base):
    __tablename__ = "bom_station"

    code = Column(Text, primary_key=True)
    state = Column(Text)
    name = Column(Text)
    registered = Column(Date)
    lat = Column(Numeric)
    lng = Column(Numeric)


class BomObservation(Base):
    __tablename__ = "bom_observation"

    observation_time = Column(DateTime, primary_key=True)

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
