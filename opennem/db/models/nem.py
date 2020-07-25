"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

from geoalchemy2 import Geometry
from sqlalchemy import (
    NUMERIC,
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

    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
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

    # @TODO id columns are all being removed and replaced with composite primaries
    # only used in dev
    id = Column(Integer, primary_key=True)

    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(Text, index=True,)
    SCADAVALUE = Column(NUMERIC(10, 6))


class NemDispatchCaseSolution(Base, NemModel):
    __tablename__ = "nem_dispatch_case_solution"
    __table_args__ = (
        Index(
            "nem_dispatch_case_solution_uniq", "SETTLEMENTDATE", unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    RUNO = Column(Integer, nullable=False)
    INTERVENTION = Column(Integer)
    CASESUBTYPE = Column(Integer)
    SOLUTIONSTATUS = Column(Integer)
    SPDVERSION = Column(Integer)
    NONPHYSICALLOSSES = Column(Integer)
    TOTALOBJECTIVE = Column(Numeric)
    TOTALAREAGENVIOLATION = Column(Integer)
    TOTALINTERCONNECTORVIOLATION = Column(Integer)
    TOTALGENERICVIOLATION = Column(Integer)
    TOTALRAMPRATEVIOLATION = Column(Integer)
    TOTALUNITMWCAPACITYVIOLATION = Column(Integer)
    TOTAL5MINVIOLATION = Column(Integer)
    TOTALREGVIOLATION = Column(Integer)
    TOTAL6SECVIOLATION = Column(Integer)
    TOTAL60SECVIOLATION = Column(Integer)
    TOTALASPROFILEVIOLATION = Column(Integer)
    TOTALFASTSTARTVIOLATION = Column(Integer)
    TOTALENERGYOFFERVIOLATION = Column(Integer)
    LASTCHANGED = Column(Integer)
    SWITCHRUNINITIALSTATUS = Column(Integer)
    SWITCHRUNBESTSTATUS = Column(Integer)
    SWITCHRUNBESTSTATUS_INT = Column(Integer)


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
    LASTCHANGED = Column(DateTime(timezone=True), nullable=False)
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

    # @TODO make enum
    OCD_STATUS = Column(Text, nullable=False)
    MII_STATUS = Column(Text, nullable=False)


class NemDispatchRegionSum(Base, NemModel):
    __tablename__ = "nem_dispatch_region_sum"
    __table_args__ = (
        # Index("nem_dispatch_region_sum_uniq", "SETTLEMENTDATE", unique=True,),
    )

    SETTLEMENTDATE = Column(Integer, nullable=False, primary_key=True)
    RUNNO = Column(Integer, nullable=False)
    REGIONID = Column(Text, nullable=False, primary_key=True)
    DISPATCHINTERVAL = Column(
        DateTime(timezone=True), nullable=False, primary_key=True
    )
    INTERVENTION = Column(Integer, nullable=False)
    TOTALDEMAND = Column(Numeric, nullable=False)
    AVAILABLEGENERATION = Column(Numeric, nullable=True)
    AVAILABLELOAD = Column(Numeric, nullable=True)
    DEMANDFORECAST = Column(Numeric, nullable=True)
    DISPATCHABLEGENERATION = Column(Numeric, nullable=True)
    DISPATCHABLELOAD = Column(Numeric, nullable=True)
    NETINTERCHANGE = Column(Numeric, nullable=True)
    EXCESSGENERATION = Column(Numeric, nullable=True)
    LOWER5MINDISPATCH = Column(Numeric, nullable=True)
    LOWER5MINIMPORT = Column(Numeric, nullable=True)
    LOWER5MINLOCALDISPATCH = Column(Numeric, nullable=True)
    LOWER5MINLOCALPRICE = Column(Numeric, nullable=True)
    LOWER5MINLOCALREQ = Column(Numeric, nullable=True)
    LOWER5MINPRICE = Column(Numeric, nullable=True)
    LOWER5MINREQ = Column(Numeric, nullable=True)
    LOWER5MINSUPPLYPRICE = Column(Numeric, nullable=True)
    LOWER60SECDISPATCH = Column(Numeric, nullable=True)
    LOWER60SECIMPORT = Column(Numeric, nullable=True)
    LOWER60SECLOCALDISPATCH = Column(Numeric, nullable=True)
    LOWER60SECLOCALPRICE = Column(Numeric, nullable=True)
    LOWER60SECLOCALREQ = Column(Numeric, nullable=True)
    LOWER60SECPRICE = Column(Numeric, nullable=True)
    LOWER60SECREQ = Column(Numeric, nullable=True)
    LOWER60SECSUPPLYPRICE = Column(Numeric, nullable=True)
    LOWER6SECDISPATCH = Column(Numeric, nullable=True)
    LOWER6SECIMPORT = Column(Numeric, nullable=True)
    LOWER6SECLOCALDISPATCH = Column(Numeric, nullable=True)
    LOWER6SECLOCALPRICE = Column(Numeric, nullable=True)
    LOWER6SECLOCALREQ = Column(Numeric, nullable=True)
    LOWER6SECPRICE = Column(Numeric, nullable=True)
    LOWER6SECREQ = Column(Numeric, nullable=True)
    LOWER6SECSUPPLYPRICE = Column(Numeric, nullable=True)
    RAISE5MINDISPATCH = Column(Numeric, nullable=True)
    RAISE5MINIMPORT = Column(Numeric, nullable=True)
    RAISE5MINLOCALDISPATCH = Column(Numeric, nullable=True)
    RAISE5MINLOCALPRICE = Column(Numeric, nullable=True)
    RAISE5MINLOCALREQ = Column(Numeric, nullable=True)
    RAISE5MINPRICE = Column(Numeric, nullable=True)
    RAISE5MINREQ = Column(Numeric, nullable=True)
    RAISE5MINSUPPLYPRICE = Column(Numeric, nullable=True)
    RAISE60SECDISPATCH = Column(Numeric, nullable=True)
    RAISE60SECIMPORT = Column(Numeric, nullable=True)
    RAISE60SECLOCALDISPATCH = Column(Numeric, nullable=True)
    RAISE60SECLOCALPRICE = Column(Numeric, nullable=True)
    RAISE60SECLOCALREQ = Column(Numeric, nullable=True)
    RAISE60SECPRICE = Column(Numeric, nullable=True)
    RAISE60SECREQ = Column(Numeric, nullable=True)
    RAISE60SECSUPPLYPRICE = Column(Numeric, nullable=True)
    RAISE6SECDISPATCH = Column(Numeric, nullable=True)
    RAISE6SECIMPORT = Column(Numeric, nullable=True)
    RAISE6SECLOCALDISPATCH = Column(Numeric, nullable=True)
    RAISE6SECLOCALPRICE = Column(Numeric, nullable=True)
    RAISE6SECLOCALREQ = Column(Numeric, nullable=True)
    RAISE6SECPRICE = Column(Numeric, nullable=True)
    RAISE6SECREQ = Column(Numeric, nullable=True)
    RAISE6SECSUPPLYPRICE = Column(Numeric, nullable=True)
    AGGEGATEDISPATCHERROR = Column(Numeric, nullable=True)
    AGGREGATEDISPATCHERROR = Column(Numeric, nullable=True)
    LASTCHANGED = Column(Numeric, nullable=True)
    INITIALSUPPLY = Column(Numeric, nullable=True)
    CLEAREDSUPPLY = Column(Numeric, nullable=True)
    LOWERREGIMPORT = Column(Numeric, nullable=True)
    LOWERREGLOCALDISPATCH = Column(Numeric, nullable=True)
    LOWERREGLOCALREQ = Column(Numeric, nullable=True)
    LOWERREGREQ = Column(Numeric, nullable=True)
    RAISEREGIMPORT = Column(Numeric, nullable=True)
    RAISEREGLOCALDISPATCH = Column(Numeric, nullable=True)
    RAISEREGLOCALREQ = Column(Numeric, nullable=True)
    RAISEREGREQ = Column(Numeric, nullable=True)
    RAISE5MINLOCALVIOLATION = Column(Numeric, nullable=True)
    RAISEREGLOCALVIOLATION = Column(Numeric, nullable=True)
    RAISE60SECLOCALVIOLATION = Column(Numeric, nullable=True)
    RAISE6SECLOCALVIOLATION = Column(Numeric, nullable=True)
    LOWER5MINLOCALVIOLATION = Column(Numeric, nullable=True)
    LOWERREGLOCALVIOLATION = Column(Numeric, nullable=True)
    LOWER60SECLOCALVIOLATION = Column(Numeric, nullable=True)
    LOWER6SECLOCALVIOLATION = Column(Numeric, nullable=True)
    RAISE5MINVIOLATION = Column(Numeric, nullable=True)
    RAISEREGVIOLATION = Column(Numeric, nullable=True)
    RAISE60SECVIOLATION = Column(Numeric, nullable=True)
    RAISE6SECVIOLATION = Column(Numeric, nullable=True)
    LOWER5MINVIOLATION = Column(Numeric, nullable=True)
    LOWERREGVIOLATION = Column(Numeric, nullable=True)
    LOWER60SECVIOLATION = Column(Numeric, nullable=True)
    LOWER6SECVIOLATION = Column(Numeric, nullable=True)
    RAISE6SECACTUALAVAILABILITY = Column(Numeric, nullable=True)
    RAISE60SECACTUALAVAILABILITY = Column(Numeric, nullable=True)
    RAISE5MINACTUALAVAILABILITY = Column(Numeric, nullable=True)
    RAISEREGACTUALAVAILABILITY = Column(Numeric, nullable=True)
    LOWER6SECACTUALAVAILABILITY = Column(Numeric, nullable=True)
    LOWER60SECACTUALAVAILABILITY = Column(Numeric, nullable=True)
    LOWER5MINACTUALAVAILABILITY = Column(Numeric, nullable=True)
    LOWERREGACTUALAVAILABILITY = Column(Numeric, nullable=True)
    LORSURPLUS = Column(Numeric, nullable=True)
    LRCSURPLUS = Column(Numeric, nullable=True)
    TOTALINTERMITTENTGENERATION = Column(Numeric, nullable=True)
    DEMAND_AND_NONSCHEDGEN = Column(Numeric, nullable=True)
    UIGF = Column(Numeric, nullable=True)
    SEMISCHEDULE_CLEAREDMW = Column(Numeric, nullable=True)
    SEMISCHEDULE_COMPLIANCEMW = Column(Numeric, nullable=True)


class NemDispatchInterconnectorRes(Base, NemModel):
    __tablename__ = "nem_dispatch_interconnector_res"
    __table_args__ = (
        # Index("nem_dispatch_interconnector_res_uniq", "SETTLEMENTDATE", unique=True,),
    )

    SETTLEMENTDATE = Column(Integer, nullable=False, primary_key=True)
    RUNNO = Column(Integer, nullable=False)
    INTERCONNECTORID = Column(Text, primary_key=True)
    DISPATCHINTERVAL = Column(DateTime(timezone=True), primary_key=True)
    INTERVENTION = Column(Numeric, nullable=True)
    METEREDMWFLOW = Column(Numeric, nullable=True)
    MWFLOW = Column(Numeric, nullable=True)
    MWLOSSES = Column(Numeric, nullable=True)
    MARGINALVALUE = Column(Numeric, nullable=True)
    VIOLATIONDEGREE = Column(Numeric, nullable=True)
    LASTCHANGED = Column(DateTime(timezone=True), nullable=False)
    EXPORTLIMIT = Column(Numeric, nullable=True)
    IMPORTLIMIT = Column(Numeric, nullable=True)
    MARGINALLOSS = Column(Numeric, nullable=True)
    EXPORTGENCONID = Column(Text, nullable=False)
    IMPORTGENCONID = Column(Text, nullable=False)
    FCASEXPORTLIMIT = Column(Numeric, nullable=True)
    FCASIMPORTLIMIT = Column(Numeric, nullable=True)
    LOCAL_PRICE_ADJUSTMENT_EXPORT = Column(Numeric, nullable=True)
    LOCALLY_CONSTRAINED_EXPORT = Column(Numeric, nullable=True)
    LOCAL_PRICE_ADJUSTMENT_IMPORT = Column(Numeric, nullable=True)
    LOCALLY_CONSTRAINED_IMPORT = Column(Numeric, nullable=True)


class NemDispatchConstraint(Base, NemModel):
    __tablename__ = "nem_dispatch_constraint"
    __table_args__ = (
        # Index("nem_dispatch_constraint_uniq", "SETTLEMENTDATE", unique=True,),
    )

    SETTLEMENTDATE = Column(Integer, nullable=False, primary_key=True)
    RUNNO = Column(Integer, nullable=False)

    CONSTRAINTID = Column(Text)
    DISPATCHINTERVAL = Column(DateTime(timezone=True), primary_key=True)
    INTERVENTION = Column(Numeric)
    RHS = Column(Numeric)
    MARGINALVALUE = Column(Integer)
    VIOLATIONDEGREE = Column(Integer)
    LASTCHANGED = Column(DateTime(timezone=True))
    DUID = Column(Text)
    GENCONID_EFFECTIVEDATE = Column(DateTime(timezone=True), nullable=True)
    GENCONID_VERSIONNO = Column(Integer, nullable=False)
    LHS = Column(Numeric, nullable=True)


class NemDispatchInterconnection(Base, NemModel):
    __tablename__ = "nem_dispatch_interconnection"
    __table_args__ = (
        # Index("nem_dispatch_region_sum_uniq", "SETTLEMENTDATE", unique=True,),
    )

    SETTLEMENTDATE = Column(Integer, nullable=False, primary_key=True)
    RUNNO = Column(Integer, nullable=False)
