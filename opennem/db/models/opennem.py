from sqlalchemy import (
    CHAR,
    DECIMAL,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Time,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class NemDispatchUnitScada(Base):
    __tablename__ = "nem_dispatch_unit_scada"
    __table_args__ = (Index("uniq", "SETTLEMENTDATE", "DUID", unique=True),)

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(
        ForeignKey("nemweb_meta.DUID.ID"),
        ForeignKey("nemweb_meta.DUID.ID"),
        index=True,
    )
    SCADAVALUE = Column(DECIMAL(10, 6))
