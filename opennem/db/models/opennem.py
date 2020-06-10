"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

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
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class NemModel(object):
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


class NemDispatchPrice(Base, NemModel):
    __tablename__ = "nem_dispatch_price"
    __table_args__ = (
        Index(
            "nem_dispatch_price_uniq", "SETTLEMENTDATE", "DUID", unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(Text, index=True,)
    SCADAVALUE = Column(NUMERIC(10, 6))

    REGIONID = Column(Text, index=True,)
    RUNO = Column(Integer, nullable=False)

    DISPATCHINTERVAL = Column(Integer, nullable=False)

    INTERVENTION = Column(Integer, nullable=False)

    RRP = Column(Integer, nullable=False)

    EEP = Column(Integer, nullable=False)

    ROP = Column(Integer, nullable=False)

    APCFLAG = Column(Integer, nullable=False)

    MARKETSUSPENDEDFLAG = Column(Integer, nullable=False)

    LASTCHANGED = Column(Integer, nullable=False)

    RAISE6SECRRP = Column(Integer, nullable=False)

    RAISE6SECROP = Column(Integer, nullable=False)

    RAISE6SECAPCFLAG = Column(Integer, nullable=False)

    RAISE60SECRRP = Column(Integer, nullable=False)

    RAISE60SECROP = Column(Integer, nullable=False)

    RAISE60SECAPCFLAG = Column(Integer, nullable=False)

    RAISE5MINRRP = Column(Integer, nullable=False)

    RAISE5MINROP = Column(Integer, nullable=False)

    RAISE5MINAPCFLAG = Column(Integer, nullable=False)

    RAISEREGRRP = Column(Integer, nullable=False)

    RAISEREGROP = Column(Integer, nullable=False)

    RAISEREGAPCFLAG = Column(Integer, nullable=False)

    LOWER6SECRRP = Column(Integer, nullable=False)

    LOWER6SECROP = Column(Integer, nullable=False)

    LOWER6SECAPCFLAG = Column(Integer, nullable=False)

    LOWER60SECRRP = Column(Integer, nullable=False)

    LOWER60SECROP = Column(Integer, nullable=False)

    LOWER60SECAPCFLAG = Column(Integer, nullable=False)

    LOWER5MINRRP = Column(Integer, nullable=False)

    LOWER5MINROP = Column(Integer, nullable=False)

    LOWER5MINAPCFLAG = Column(Integer, nullable=False)

    LOWERREGRRP = Column(Integer, nullable=False)

    LOWERREGROP = Column(Integer, nullable=False)

    LOWERREGAPCFLAG = Column(Integer, nullable=False)

    PRICE_STATUS = Column(Integer, nullable=False)

    PRE_AP_ENERGY_PRICE = Column(Integer, nullable=False)

    PRE_AP_RAISE6_PRICE = Column(Integer, nullable=False)

    PRE_AP_RAISE60_PRICE = Column(Integer, nullable=False)

    PRE_AP_RAISE5MIN_PRICE = Column(Integer, nullable=False)

    PRE_AP_RAISEREG_PRICE = Column(Integer, nullable=False)

    PRE_AP_LOWER6_PRICE = Column(Integer, nullable=False)

    PRE_AP_LOWER60_PRICE = Column(Integer, nullable=False)

    PRE_AP_LOWER5MIN_PRICE = Column(Integer, nullable=False)

    PRE_AP_LOWERREG_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_ENERGY_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_RAISE6_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_RAISE60_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_RAISE5MIN_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_RAISEREG_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_LOWER6_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_LOWER60_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_LOWER5MIN_PRICE = Column(Integer, nullable=False)

    CUMUL_PRE_AP_LOWERREG_PRICE = Column(Integer, nullable=False)

    OCD_STATUS = Column(Integer, nullable=False)

    MII_STATUS = Column(Integer, nullable=False)


class WemFacilityScada(Base, NemModel):
    __tablename__ = "wem_facility_scada"
    __table_args__ = (
        Index(
            "wem_facility_scada_uniq",
            "TRADING_INTERVAL",
            "FACILITY_CODE",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    TRADING_INTERVAL = Column(DateTime, index=True)
    PARTICIPANT_CODE = Column(Text, index=True,)
    FACILITY_CODE = Column(Text, index=True,)
    ENERGY_GENERATED = Column(NUMERIC(10, 6))
    EOI_QUANTITY = Column(NUMERIC(10, 6))
