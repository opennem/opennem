from sqlalchemy import (
    NUMERIC,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class NemModel(object):
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key == "id" or key.endswith("_id"):
                continue

            # @TODO watch how we do updates so we don't overwrite data
            cur_val = getattr(self, key)
            if key not in [None, ""]:
                setattr(self, key, value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NemDispatchUnitScada(Base, NemModel):
    __tablename__ = "nem_dispatch_unit_scada"
    __table_args__ = (
        Index(
            "nem_dispatch_unit_scada_uniq",
            "SETTLEMENTDATE",
            "DUID",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(Text, index=True,)
    SCADAVALUE = Column(NUMERIC(10, 6))
