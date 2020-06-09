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
from sqlalchemy.dialects.mysql import (
    BIGINT,
    INTEGER,
    MEDIUMINT,
    SMALLINT,
    TINYINT,
    VARCHAR,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class BIDTYPE(Base):
    __tablename__ = "BIDTYPE"

    ID = Column(TINYINT(4), primary_key=True)
    BIDTYPE = Column(String(10))


t_DUID = Table(
    "DUID",
    metadata,
    Column("id", SMALLINT(6), server_default=text("'0'")),
    Column("DUID", String(10)),
    Column("STATION_NAME_ID", SMALLINT(6)),
    Column("PARTICIPANT_ID", SMALLINT(6)),
    Column("REGIONID", TINYINT(4)),
    Column("FUEL_SOURCE_ID", TINYINT(4)),
    Column("TECHNOLOGY_ID", TINYINT(4)),
    Column("CLASSIFICATION_ID", TINYINT(4)),
    Column("TECHFUEL_ID", TINYINT(4), server_default=text("'0'")),
    Column("MW", DECIMAL(29, 3)),
)


class DispatchedMarket(Base):
    __tablename__ = "DispatchedMarket"

    ID = Column(TINYINT(4), primary_key=True)
    DispatchedMarket = Column(String(30))


t_INTERCONNECTORID = Table(
    "INTERCONNECTORID",
    metadata,
    Column("id", TINYINT(4), server_default=text("'0'")),
    Column("INTERCONNECTORID", String(9)),
)


class INTERVALTABLE(Base):
    __tablename__ = "INTERVAL_TABLE"

    DISPATCHINTERVAL = Column(BIGINT(20), primary_key=True)
    TRADINGINTERVAL = Column(INTEGER(11), nullable=False, index=True)
    DATETIME = Column(DateTime, nullable=False, index=True)
    DATE = Column(Date, nullable=False, index=True)
    TIME = Column(Time, nullable=False, index=True)
    DISPATCHPERIOD = Column(SMALLINT(6), nullable=False, index=True)
    TRADINGPERIOD = Column(TINYINT(4), nullable=False, index=True)
    YEAR = Column(SMALLINT(6), nullable=False, index=True)
    MONTH = Column(TINYINT(4), nullable=False, index=True)
    WEEKDAY = Column(TINYINT(4), nullable=False, index=True)
    FY = Column(TINYINT(4), nullable=False, index=True)
    PEAK = Column(TINYINT(4), nullable=False)


class Market(Base):
    __tablename__ = "Market"

    ID = Column(TINYINT(4), primary_key=True)
    Market = Column(String(8))


t_REGIONID = Table(
    "REGIONID",
    metadata,
    Column("id", TINYINT(4), server_default=text("'0'")),
    Column("REGIONID", String(6)),
)


class RUNTYPE(Base):
    __tablename__ = "RUNTYPE"

    ID = Column(TINYINT(4), primary_key=True)
    RUNTYPE = Column(String(45), unique=True)


class Unit(Base):
    __tablename__ = "Unit"

    ID = Column(SMALLINT(6), primary_key=True)
    Unit = Column(VARCHAR(30), unique=True)


class DUID(Base):
    __tablename__ = "DUID"
    __table_args__ = {"schema": "nemweb_meta"}

    ID = Column(SMALLINT(6), primary_key=True)
    DUID = Column(VARCHAR(10), unique=True)


class REGIONID(Base):
    __tablename__ = "REGIONID"
    __table_args__ = {"schema": "nemweb_meta"}

    id = Column(TINYINT(4), primary_key=True)
    REGIONID = Column(VARCHAR(6), unique=True)


class CO2EIIPUBLISHING(Base):
    __tablename__ = "CO2EII_PUBLISHING"
    __table_args__ = (
        Index("SETTLEMENTDATE_2", "SETTLEMENTDATE", "REGIONID", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    CONTRACTYEAR = Column(SMALLINT(6), index=True)
    WEEKNO = Column(TINYINT(4), index=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    TOTAL_SENT_OUT_ENERGY = Column(DECIMAL(14, 8))
    TOTAL_EMISSIONS = Column(DECIMAL(14, 8))
    CO2E_INTENSITY_INDEX = Column(DECIMAL(5, 4))

    REGIONID1 = relationship("REGIONID")


class DISPATCHPRICE(Base):
    __tablename__ = "DISPATCH_PRICE"
    __table_args__ = (
        Index(
            "uniq", "SETTLEMENTDATE", "REGIONID", "INTERVENTION", unique=True
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DISPATCHINTERVAL = Column(BIGINT(20), index=True)
    RRP = Column(DECIMAL(10, 5))
    ROP = Column(DECIMAL(12, 5))
    APCFLAG = Column(TINYINT(4), index=True)
    CUMUL_PRE_AP_ENERGY_PRICE = Column(DECIMAL(16, 10))
    INTERVENTION = Column(
        TINYINT(4), nullable=False, index=True, server_default=text("0")
    )
    RAISE6SECRRP = Column(DECIMAL(12, 5))
    RAISE6SECROP = Column(DECIMAL(12, 5))
    RAISE6SECAPCFLAG = Column(TINYINT(4), index=True)
    RAISE60SECRRP = Column(DECIMAL(12, 5))
    RAISE60SECROP = Column(DECIMAL(12, 5))
    RAISE60SECAPCFLAG = Column(TINYINT(4), index=True)
    RAISE5MINRRP = Column(DECIMAL(12, 5))
    RAISE5MINROP = Column(DECIMAL(12, 5))
    RAISE5MINAPCFLAG = Column(TINYINT(4), index=True)
    RAISEREGRRP = Column(DECIMAL(12, 5))
    RAISEREGROP = Column(DECIMAL(12, 5))
    RAISEREGAPCFLAG = Column(TINYINT(4), index=True)
    LOWER6SECRRP = Column(DECIMAL(12, 5))
    LOWER6SECROP = Column(DECIMAL(12, 5))
    LOWER6SECAPCFLAG = Column(TINYINT(4), index=True)
    LOWER60SECRRP = Column(DECIMAL(12, 5))
    LOWER60SECROP = Column(DECIMAL(12, 5))
    LOWER60SECAPCFLAG = Column(TINYINT(4), index=True)
    LOWER5MINRRP = Column(DECIMAL(12, 5))
    LOWER5MINROP = Column(DECIMAL(12, 5))
    LOWER5MINAPCFLAG = Column(TINYINT(4), index=True)
    LOWERREGRRP = Column(DECIMAL(12, 5))
    LOWERREGROP = Column(DECIMAL(12, 5))
    LOWERREGAPCFLAG = Column(TINYINT(4), index=True)

    REGIONID1 = relationship("REGIONID")


class DISPATCHREGIONSUM(Base):
    __tablename__ = "DISPATCH_REGIONSUM"
    __table_args__ = (
        Index(
            "uniq", "REGIONID", "SETTLEMENTDATE", "INTERVENTION", unique=True
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    TOTALDEMAND = Column(DECIMAL(7, 2))
    AVAILABLEGENERATION = Column(DECIMAL(10, 5))
    AVAILABLELOAD = Column(DECIMAL(7, 2))
    DEMANDFORECAST = Column(DECIMAL(10, 5))
    DISPATCHABLEGENERATION = Column(DECIMAL(7, 2))
    DISPATCHABLELOAD = Column(DECIMAL(7, 2))
    NETINTERCHANGE = Column(DECIMAL(6, 2))
    EXCESSGENERATION = Column(DECIMAL(7, 2))
    INITIALSUPPLY = Column(DECIMAL(10, 5))
    CLEAREDSUPPLY = Column(DECIMAL(7, 2))
    TOTALINTERMITTENTGENERATION = Column(DECIMAL(10, 5))
    DEMAND_AND_NONSCHEDGEN = Column(DECIMAL(10, 5))
    UIGF = Column(DECIMAL(10, 5))
    SEMISCHEDULE_CLEAREDMW = Column(DECIMAL(10, 5))
    DISPATCHINTERVAL = Column(BIGINT(20), index=True)
    SEMISCHEDULE_COMPLIANCEMW = Column(DECIMAL(10, 5))
    INTERVENTION = Column(
        TINYINT(4), nullable=False, index=True, server_default=text("0")
    )
    LOWERREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER6SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISEREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE6SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    AGGREGATEDISPATCHERROR = Column(DECIMAL(10, 5))
    RAISE6SECACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    RAISE5MINACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    RAISE60SECACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    RAISEREGACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    LOWER6SECACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    LOWER5MINACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    LOWER60SECACTUALAVAILABILITY = Column(DECIMAL(12, 6))
    LOWERREGACTUALAVAILABILITY = Column(DECIMAL(12, 6))

    REGIONID1 = relationship("REGIONID")


class DISPATCHUNITSCADA(Base):
    __tablename__ = "DISPATCH_UNIT_SCADA"
    __table_args__ = (Index("uniq", "SETTLEMENTDATE", "DUID", unique=True),)

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(
        ForeignKey("nemweb_meta.DUID.ID"),
        ForeignKey("nemweb_meta.DUID.ID"),
        index=True,
    )
    SCADAVALUE = Column(DECIMAL(10, 6))

    DUID1 = relationship(
        "DUID", primaryjoin="DISPATCHUNITSCADA.DUID == DUID.ID"
    )
    DUID2 = relationship(
        "DUID", primaryjoin="DISPATCHUNITSCADA.DUID == DUID.ID"
    )


class DISPATCHUNITSOLUTION(Base):
    __tablename__ = "DISPATCH_UNIT_SOLUTION"
    __table_args__ = (
        Index(
            "uniq_idx", "DUID", "SETTLEMENTDATE", "INTERVENTION", unique=True
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    INTERVENTION = Column(TINYINT(4), index=True)
    DISPATCHMODE = Column(TINYINT(4), index=True)
    AGCSTATUS = Column(TINYINT(4), index=True)
    INITIALMW = Column(DECIMAL(10, 6))
    TOTALCLEARED = Column(DECIMAL(10, 6))
    RAMPDOWNRATE = Column(DECIMAL(8, 2))
    RAMPUPRATE = Column(DECIMAL(8, 2))
    LOWER5MIN = Column(DECIMAL(10, 6))
    LOWER60SEC = Column(DECIMAL(10, 6))
    LOWER6SEC = Column(DECIMAL(10, 6))
    RAISE5MIN = Column(DECIMAL(10, 6))
    RAISE60SEC = Column(DECIMAL(10, 6))
    RAISE6SEC = Column(DECIMAL(10, 6))
    LOWERREG = Column(DECIMAL(10, 6))
    RAISEREG = Column(DECIMAL(10, 6))
    AVAILABILITY = Column(DECIMAL(10, 6))

    DUID1 = relationship("DUID")


class DISPATCHUNITSOLUTIONOLD(Base):
    __tablename__ = "DISPATCH_UNIT_SOLUTION_OLD"
    __table_args__ = (
        Index("uniq", "SETTLEMENTDATE", "DUID", "INTERVENTION", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    INITIALMW = Column(DECIMAL(10, 6))
    TOTALCLEARED = Column(DECIMAL(10, 6))
    INTERVENTION = Column(SMALLINT(6), index=True)

    DUID1 = relationship("DUID")


class METERDATAGENDUID(Base):
    __tablename__ = "METER_DATA_GEN_DUID"
    __table_args__ = (
        Index("DUID_2", "DUID", "INTERVAL_DATETIME", unique=True),
    )

    ID = Column(INTEGER(11), primary_key=True)
    INTERVAL_DATETIME = Column(DateTime, index=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    MWH_READING = Column(DECIMAL(10, 6))

    DUID1 = relationship("DUID")


class MTPASAREGIONSOLUTION(Base):
    __tablename__ = "MTPASA_REGIONSOLUTION"
    __table_args__ = (
        Index(
            "uniq",
            "RUN_DATETIME",
            "RUN_NO",
            "DAY",
            "REGIONID",
            "RUNTYPE",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    RUN_DATETIME = Column(DateTime, index=True)
    RUN_NO = Column(INTEGER(11), index=True)
    RUNTYPE = Column(ForeignKey("RUNTYPE.ID"), index=True)
    DAY = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    DEMAND10 = Column(DECIMAL(12, 2))
    ENERGYREQDEMAND10 = Column(DECIMAL(12, 2))
    UNCONSTRAINEDCAPACITY = Column(DECIMAL(12, 0))
    CONSTRAINEDCAPACITY = Column(DECIMAL(12, 0))
    NETINTERCHANGEUNDERSCARCITY = Column(DECIMAL(12, 2))
    SURPLUSCAPACITY = Column(DECIMAL(12, 2))
    RESERVECONDITION = Column(TINYINT(4))
    MAXSURPLUSRESERVE = Column(DECIMAL(12, 2))
    MAXSPARECAPACITY = Column(DECIMAL(12, 2))
    LORCONDITION = Column(TINYINT(4))
    AGGREGATECAPACITYAVAILABLE = Column(DECIMAL(12, 2))
    AGGREGATESCHEDULEDLOAD = Column(DECIMAL(12, 2))
    AGGREGATEPASAAVAILABILITY = Column(DECIMAL(12, 0))
    TOTALINTERMITTENTGENERATION = Column(DECIMAL(10, 5))
    DEMAND50 = Column(DECIMAL(12, 2))
    DEMAND_AND_NONSCHEDGEN = Column(DECIMAL(15, 5))
    UIGF = Column(DECIMAL(12, 2))
    SEMISCHEDULEDCAPACITY = Column(DECIMAL(12, 2))
    DEFICITRESERVE = Column(DECIMAL(16, 6))
    ENERGYREQDEMAND50 = Column(DECIMAL(12, 2))

    REGIONID1 = relationship("REGIONID")
    RUNTYPE1 = relationship("RUNTYPE")


class NEMPriceSetter(Base):
    __tablename__ = "NEMPriceSetter"
    __table_args__ = (
        Index(
            "uniq_idx",
            "Market",
            "Unit",
            "Unit_2",
            "PeriodID",
            "REGIONID",
            "DispatchedMarket",
            "OCD_flag",
            "BandNo",
            "BandNo_2",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    PeriodID = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    Market = Column(ForeignKey("Market.ID"), index=True)
    DispatchedMarket = Column(ForeignKey("DispatchedMarket.ID"), index=True)
    Price = Column(DECIMAL(12, 5))
    Unit = Column(ForeignKey("Unit.ID"), index=True)
    BandNo = Column(TINYINT(4))
    Unit_2 = Column(ForeignKey("Unit.ID"), index=True)
    BandNo_2 = Column(TINYINT(4))
    Increase = Column(DECIMAL(12, 5))
    RRNBandPrice = Column(DECIMAL(10, 2))
    BandCost = Column(DECIMAL(14, 6))
    OCD_flag = Column(TINYINT(4), index=True, server_default=text("0"))

    DispatchedMarket1 = relationship("DispatchedMarket")
    Market1 = relationship("Market")
    REGIONID1 = relationship("REGIONID")
    Unit1 = relationship("Unit", primaryjoin="NEMPriceSetter.Unit == Unit.ID")
    Unit2 = relationship(
        "Unit", primaryjoin="NEMPriceSetter.Unit_2 == Unit.ID"
    )


class OFFERBIDDAYOFFER(Base):
    __tablename__ = "OFFER_BIDDAYOFFER"

    ID = Column(INTEGER(11), primary_key=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    OFFERDATE = Column(DateTime, index=True)
    VERSIONNO = Column(SMALLINT(6), index=True)
    BIDTYPE = Column(ForeignKey("BIDTYPE.ID"), index=True)
    DAILYENERGYCONSTRAINT = Column(INTEGER(11))
    PRICEBAND1 = Column(DECIMAL(7, 2))
    PRICEBAND2 = Column(DECIMAL(7, 2))
    PRICEBAND3 = Column(DECIMAL(7, 2))
    PRICEBAND4 = Column(DECIMAL(7, 2))
    PRICEBAND5 = Column(DECIMAL(7, 2))
    PRICEBAND6 = Column(DECIMAL(7, 2))
    PRICEBAND7 = Column(DECIMAL(7, 2))
    PRICEBAND8 = Column(DECIMAL(7, 2))
    PRICEBAND9 = Column(DECIMAL(7, 2))
    PRICEBAND10 = Column(DECIMAL(7, 2))
    MINIMUMLOAD = Column(MEDIUMINT(9))
    LASTCHANGED = Column(DateTime, index=True)
    ENTRYTYPE = Column(CHAR(5), index=True)
    T1 = Column(TINYINT(4))
    T2 = Column(TINYINT(4))
    T3 = Column(TINYINT(4))
    T4 = Column(TINYINT(4))

    BIDTYPE1 = relationship("BIDTYPE")
    DUID1 = relationship("DUID")


class OFFERBIDPEROFFER(Base):
    __tablename__ = "OFFER_BIDPEROFFER"

    ID = Column(INTEGER(11), primary_key=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    OFFERDATE = Column(DateTime, index=True)
    PERIODID = Column(TINYINT(4), index=True)
    VERSIONNO = Column(MEDIUMINT(9), index=True)
    BIDTYPE = Column(ForeignKey("BIDTYPE.ID"), index=True)
    MAXAVAIL = Column(MEDIUMINT(9))
    ROCUP = Column(SMALLINT(6))
    ROCDOWN = Column(SMALLINT(6))
    BANDAVAIL1 = Column(SMALLINT(6))
    BANDAVAIL2 = Column(SMALLINT(6))
    BANDAVAIL3 = Column(SMALLINT(6))
    BANDAVAIL4 = Column(SMALLINT(6))
    BANDAVAIL5 = Column(SMALLINT(6))
    BANDAVAIL6 = Column(SMALLINT(6))
    BANDAVAIL7 = Column(SMALLINT(6))
    BANDAVAIL8 = Column(SMALLINT(6))
    BANDAVAIL9 = Column(SMALLINT(6))
    BANDAVAIL10 = Column(SMALLINT(6))
    LASTCHANGED = Column(DateTime, index=True)

    BIDTYPE1 = relationship("BIDTYPE")
    DUID1 = relationship("DUID")


class P5MINREGIONSOLUTION(Base):
    __tablename__ = "P5MIN_REGIONSOLUTION"
    __table_args__ = (
        Index(
            "uniq",
            "RUN_DATETIME",
            "INTERVAL_DATETIME",
            "REGIONID",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    RUN_DATETIME = Column(DateTime, index=True)
    INTERVAL_DATETIME = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    RRP = Column(DECIMAL(10, 5))
    EXCESSGENERATION = Column(DECIMAL(7, 2))
    RAISE6SECRRP = Column(DECIMAL(10, 5))
    RAISE60SECRRP = Column(DECIMAL(10, 5))
    RAISE5MINRRP = Column(DECIMAL(10, 5))
    RAISEREGRRP = Column(DECIMAL(10, 5))
    LOWER6SECRRP = Column(DECIMAL(10, 5))
    LOWER60SECRRP = Column(DECIMAL(10, 5))
    LOWER5MINRRP = Column(DECIMAL(10, 5))
    LOWERREGRRP = Column(DECIMAL(10, 5))
    TOTALDEMAND = Column(DECIMAL(7, 2))
    AVAILABLEGENERATION = Column(DECIMAL(8, 3))
    AVAILABLELOAD = Column(DECIMAL(7, 3))
    DEMANDFORECAST = Column(DECIMAL(10, 5))
    DISPATCHABLEGENERATION = Column(DECIMAL(7, 2))
    DISPATCHABLELOAD = Column(DECIMAL(7, 2))
    NETINTERCHANGE = Column(DECIMAL(7, 2))
    LOWER5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER6SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE6SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    AGGREGATEDISPATCHERROR = Column(DECIMAL(10, 5))
    INITIALSUPPLY = Column(DECIMAL(10, 5))
    CLEAREDSUPPLY = Column(DECIMAL(7, 2))
    LOWERREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISEREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    TOTALINTERMITTENTGENERATION = Column(DECIMAL(8, 3))
    DEMAND_AND_NONSCHEDGEN = Column(DECIMAL(8, 3))
    UIGF = Column(DECIMAL(8, 3))
    SEMISCHEDULE_CLEAREDMW = Column(DECIMAL(9, 4))
    SEMISCHEDULE_COMPLIANCEMW = Column(DECIMAL(9, 4))

    REGIONID1 = relationship("REGIONID")


class PREDISPATCHPRICESENSITIVITY(Base):
    __tablename__ = "PREDISPATCH_PRICESENSITIVITIES"
    __table_args__ = (
        Index(
            "uniq_idx",
            "PREDISPATCHSEQNO",
            "REGIONID",
            "PERIODID",
            "INTERVENTION",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    PREDISPATCHSEQNO = Column(BIGINT(20), index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    PERIODID = Column(TINYINT(4), index=True)
    INTERVENTION = Column(TINYINT(4), index=True)
    INTERVENTION_ACTIVE = Column(TINYINT(4), index=True)
    DATETIME = Column(DateTime, index=True)
    RRPEEP1 = Column(DECIMAL(12, 6))
    RRPEEP2 = Column(DECIMAL(12, 6))
    RRPEEP3 = Column(DECIMAL(12, 6))
    RRPEEP4 = Column(DECIMAL(12, 6))
    RRPEEP5 = Column(DECIMAL(12, 6))
    RRPEEP6 = Column(DECIMAL(12, 6))
    RRPEEP7 = Column(DECIMAL(12, 6))
    RRPEEP8 = Column(DECIMAL(12, 6))
    RRPEEP9 = Column(DECIMAL(12, 6))
    RRPEEP10 = Column(DECIMAL(12, 6))
    RRPEEP11 = Column(DECIMAL(12, 6))
    RRPEEP12 = Column(DECIMAL(12, 6))
    RRPEEP13 = Column(DECIMAL(12, 6))
    RRPEEP14 = Column(DECIMAL(12, 6))
    RRPEEP15 = Column(DECIMAL(12, 6))
    RRPEEP16 = Column(DECIMAL(12, 6))
    RRPEEP17 = Column(DECIMAL(12, 6))
    RRPEEP18 = Column(DECIMAL(12, 6))
    RRPEEP19 = Column(DECIMAL(12, 6))
    RRPEEP20 = Column(DECIMAL(12, 6))
    RRPEEP21 = Column(DECIMAL(12, 6))
    RRPEEP22 = Column(DECIMAL(12, 6))
    RRPEEP23 = Column(DECIMAL(12, 6))
    RRPEEP24 = Column(DECIMAL(12, 6))
    RRPEEP25 = Column(DECIMAL(12, 6))
    RRPEEP26 = Column(DECIMAL(12, 6))
    RRPEEP27 = Column(DECIMAL(12, 6))
    RRPEEP28 = Column(DECIMAL(12, 6))
    RRPEEP29 = Column(DECIMAL(12, 6))
    RRPEEP30 = Column(DECIMAL(12, 6))
    RRPEEP31 = Column(DECIMAL(12, 6))
    RRPEEP32 = Column(DECIMAL(12, 6))
    RRPEEP33 = Column(DECIMAL(12, 6))
    RRPEEP34 = Column(DECIMAL(12, 6))
    RRPEEP35 = Column(DECIMAL(12, 6))
    RRPEEP36 = Column(DECIMAL(12, 6))
    RRPEEP37 = Column(DECIMAL(12, 6))
    RRPEEP38 = Column(DECIMAL(12, 6))
    RRPEEP39 = Column(DECIMAL(12, 6))
    RRPEEP40 = Column(DECIMAL(12, 6))
    RRPEEP41 = Column(DECIMAL(12, 6))
    RRPEEP42 = Column(DECIMAL(12, 6))
    RRPEEP43 = Column(DECIMAL(12, 6))
    LASTCHANGED = Column(DateTime)

    REGIONID1 = relationship("REGIONID")


class PREDISPATCHREGIONPRICE(Base):
    __tablename__ = "PREDISPATCH_REGION_PRICES"
    __table_args__ = (
        Index(
            "uniq",
            "REGIONID",
            "PREDISPATCHSEQNO",
            "INTERVENTION",
            "PERIODID",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    PREDISPATCHSEQNO = Column(INTEGER(11), index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    PERIODID = Column(TINYINT(4), index=True)
    RRP = Column(DECIMAL(10, 5))
    DATETIME = Column(DateTime, index=True)
    INTERVENTION = Column(TINYINT(4), nullable=False, index=True)
    RAISE60SECRRP = Column(DECIMAL(10, 5))
    RAISE5MINRRP = Column(DECIMAL(10, 5))
    RAISEREGRRP = Column(DECIMAL(10, 5))
    RAISE6SECRRP = Column(DECIMAL(10, 5))
    LOWER6SECRRP = Column(DECIMAL(10, 5))
    LOWER60SECRRP = Column(DECIMAL(10, 5))
    LOWER5MINRRP = Column(DECIMAL(10, 5))
    LOWERREGRRP = Column(DECIMAL(10, 5))

    REGIONID1 = relationship("REGIONID")


class PREDISPATCHREGIONSOLUTION(Base):
    __tablename__ = "PREDISPATCH_REGION_SOLUTION"
    __table_args__ = (
        Index(
            "uniq",
            "REGIONID",
            "PREDISPATCHSEQNO",
            "INTERVENTION",
            "PERIODID",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    PREDISPATCHSEQNO = Column(INTEGER(11), index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    TOTALDEMAND = Column(DECIMAL(7, 2))
    AVAILABLEGENERATION = Column(DECIMAL(8, 3))
    AVAILABLELOAD = Column(DECIMAL(7, 3))
    DEMANDFORECAST = Column(DECIMAL(10, 5))
    DISPATCHABLEGENERATION = Column(DECIMAL(7, 2))
    DISPATCHABLELOAD = Column(DECIMAL(7, 2))
    NETINTERCHANGE = Column(DECIMAL(7, 2), nullable=False)
    EXCESSGENERATION = Column(DECIMAL(7, 2))
    DATETIME = Column(DateTime, index=True)
    INITIALSUPPLY = Column(DECIMAL(10, 5))
    CLEAREDSUPPLY = Column(DECIMAL(7, 2))
    TOTALINTERMITTENTGENERATION = Column(DECIMAL(8, 3))
    DEMAND_AND_NONSCHEDGEN = Column(DECIMAL(8, 3))
    UIGF = Column(DECIMAL(8, 3))
    SEMISCHEDULE_CLEAREDMW = Column(DECIMAL(9, 4), nullable=False)
    SEMISCHEDULE_COMPLIANCEMW = Column(DECIMAL(9, 4))
    PERIODID = Column(TINYINT(4), index=True)
    INTERVENTION = Column(TINYINT(4), nullable=False, index=True)

    REGIONID1 = relationship("REGIONID")


class ROOFTOPACTUAL(Base):
    __tablename__ = "ROOFTOP_ACTUAL"
    __table_args__ = (
        Index("uniq_idx", "INTERVAL_DATETIME", "REGIONID", unique=True),
    )

    ID = Column(INTEGER(11), primary_key=True)
    INTERVAL_DATETIME = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    POWER = Column(DECIMAL(8, 3))

    REGIONID1 = relationship("REGIONID")


class ROOFTOPFORECAST(Base):
    __tablename__ = "ROOFTOP_FORECAST"
    __table_args__ = (
        Index(
            "uniq_idx",
            "VERSION_DATETIME",
            "INTERVAL_DATETIME",
            "REGIONID",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    VERSION_DATETIME = Column(DateTime, index=True)
    INTERVAL_DATETIME = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    POWERMEAN = Column(DECIMAL(8, 3))
    POWERPOE50 = Column(DECIMAL(8, 3))
    POWERPOELOW = Column(DECIMAL(8, 3))
    POWERPOEHIGH = Column(DECIMAL(8, 3))

    REGIONID1 = relationship("REGIONID")


class TRADINGPRICE(Base):
    __tablename__ = "TRADING_PRICE"
    __table_args__ = (
        Index("uniq", "SETTLEMENTDATE", "REGIONID", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, nullable=False, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    RRP = Column(DECIMAL(7, 2))
    ROP = Column(DECIMAL(8, 2))
    RAISE6SECRRP = Column(DECIMAL(12, 5))
    RAISE6SECROP = Column(DECIMAL(12, 5))
    RAISE60SECRRP = Column(DECIMAL(12, 5))
    RAISE60SECROP = Column(DECIMAL(12, 5))
    RAISE5MINRRP = Column(DECIMAL(12, 5))
    RAISE5MINROP = Column(DECIMAL(12, 5))
    RAISEREGRRP = Column(DECIMAL(12, 5))
    RAISEREGROP = Column(DECIMAL(12, 5))
    LOWER6SECRRP = Column(DECIMAL(12, 5))
    LOWER6SECROP = Column(DECIMAL(12, 5))
    LOWER60SECRRP = Column(DECIMAL(12, 5))
    LOWER60SECROP = Column(DECIMAL(12, 5))
    LOWER5MINRRP = Column(DECIMAL(12, 5))
    LOWER5MINROP = Column(DECIMAL(12, 5))
    LOWERREGRRP = Column(DECIMAL(12, 5))
    LOWERREGROP = Column(DECIMAL(12, 5))

    REGIONID1 = relationship("REGIONID")


class TRADINGREGIONSUM(Base):
    __tablename__ = "TRADING_REGIONSUM"
    __table_args__ = (
        Index("uniq", "SETTLEMENTDATE", "REGIONID", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    TOTALDEMAND = Column(DECIMAL(7, 2))
    AVAILABLEGENERATION = Column(DECIMAL(7, 2))
    AVAILABLELOAD = Column(DECIMAL(7, 2))
    DEMANDFORECAST = Column(DECIMAL(7, 2))
    DISPATCHABLEGENERATION = Column(DECIMAL(7, 2))
    DISPATCHABLELOAD = Column(DECIMAL(7, 2))
    NETINTERCHANGE = Column(DECIMAL(7, 2))
    EXCESSGENERATION = Column(DECIMAL(7, 2))
    INITIALSUPPLY = Column(DECIMAL(7, 2))
    CLEAREDSUPPLY = Column(DECIMAL(7, 2))
    TOTALINTERMITTENTGENERATION = Column(DECIMAL(7, 2))
    DEMAND_AND_NONSCHEDGEN = Column(DECIMAL(7, 2))
    UIGF = Column(DECIMAL(7, 2))
    LOWERREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    LOWER6SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE5MINLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISEREGLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE60SECLOCALDISPATCH = Column(DECIMAL(10, 5))
    RAISE6SECLOCALDISPATCH = Column(DECIMAL(10, 5))

    REGIONID1 = relationship("REGIONID")


class YESTBIDBIDDAYOFFER(Base):
    __tablename__ = "YESTBID_BIDDAYOFFER"
    __table_args__ = (
        Index(
            "uniq",
            "DUID",
            "LASTCHANGED",
            "BIDOFFERDATE",
            "BIDTYPE",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    BIDOFFERDATE = Column(DateTime, index=True)
    PRICEBAND1 = Column(DECIMAL(7, 2))
    PRICEBAND2 = Column(DECIMAL(7, 2))
    PRICEBAND3 = Column(DECIMAL(7, 2))
    PRICEBAND4 = Column(DECIMAL(7, 2))
    PRICEBAND5 = Column(DECIMAL(7, 2), nullable=False)
    PRICEBAND6 = Column(DECIMAL(7, 2))
    PRICEBAND7 = Column(DECIMAL(7, 2))
    PRICEBAND8 = Column(DECIMAL(7, 2))
    PRICEBAND9 = Column(DECIMAL(7, 2), nullable=False)
    PRICEBAND10 = Column(DECIMAL(7, 2))
    MINIMUMLOAD = Column(SMALLINT(6))
    LASTCHANGED = Column(DateTime, index=True)
    BIDVERSIONNO = Column(SMALLINT(6))
    ENTRYTYPE = Column(String(10), index=True)
    BIDTYPE = Column(ForeignKey("BIDTYPE.ID"), index=True)
    BIDSETTLEMENTDATE = Column(DateTime)
    DAILYENERGYCONSTRAINT = Column(DECIMAL(12, 6))

    BIDTYPE1 = relationship("BIDTYPE")
    DUID1 = relationship("DUID")


class YESTBIDBIDPEROFFER(Base):
    __tablename__ = "YESTBID_BIDPEROFFER"
    __table_args__ = (
        Index(
            "uniq",
            "DUID",
            "TRADINGPERIOD",
            "LASTCHANGED",
            "BIDTYPE",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    DUID = Column(ForeignKey("nemweb_meta.DUID.ID"), index=True)
    BIDOFFERDATE = Column(DateTime, index=True)
    TRADINGPERIOD = Column(DateTime, index=True)
    MAXAVAIL = Column(SMALLINT(6))
    FIXEDLOAD = Column(SMALLINT(6))
    ROCUP = Column(SMALLINT(6))
    ROCDOWN = Column(SMALLINT(6))
    BANDAVAIL1 = Column(SMALLINT(6))
    BANDAVAIL2 = Column(SMALLINT(6))
    BANDAVAIL3 = Column(SMALLINT(6))
    BANDAVAIL4 = Column(SMALLINT(6))
    BANDAVAIL5 = Column(SMALLINT(6))
    BANDAVAIL6 = Column(SMALLINT(6))
    BANDAVAIL7 = Column(SMALLINT(6))
    BANDAVAIL8 = Column(SMALLINT(6))
    BANDAVAIL9 = Column(SMALLINT(6))
    BANDAVAIL10 = Column(SMALLINT(6))
    PASAAVAILABILITY = Column(SMALLINT(6))
    PERIODID = Column(TINYINT(4), nullable=False, index=True)
    LASTCHANGED = Column(DateTime, index=True)
    BIDVERSIONNO = Column(SMALLINT(6))
    SETTLEMENTDATE = Column(DateTime)
    BIDTYPE = Column(ForeignKey("BIDTYPE.ID"), index=True)
    BIDSETTLEMENTDATE = Column(DateTime)
    ENABLEMENTMIN = Column(DECIMAL(6, 0))
    ENABLEMENTMAX = Column(DECIMAL(6, 0))
    HIGHBREAKPOINT = Column(DECIMAL(6, 0))
    LOWBREAKPOINT = Column(DECIMAL(6, 0))

    BIDTYPE1 = relationship("BIDTYPE")
    DUID1 = relationship("DUID")


class INTERCONNECTORID(Base):
    __tablename__ = "INTERCONNECTORID"
    __table_args__ = {"schema": "nemweb_meta"}

    id = Column(TINYINT(4), primary_key=True)
    INTERCONNECTORID = Column(VARCHAR(9), nullable=False, unique=True)
    FROM_REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)
    TO_REGIONID = Column(ForeignKey("nemweb_meta.REGIONID.id"), index=True)

    REGIONID = relationship(
        "REGIONID", primaryjoin="INTERCONNECTORID.FROM_REGIONID == REGIONID.id"
    )
    REGIONID1 = relationship(
        "REGIONID", primaryjoin="INTERCONNECTORID.TO_REGIONID == REGIONID.id"
    )


class DISPATCHINTERCONNECTORRE(Base):
    __tablename__ = "DISPATCH_INTERCONNECTORRES"
    __table_args__ = (
        Index(
            "uniq",
            "INTERCONNECTORID",
            "SETTLEMENTDATE",
            "INTERVENTION",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    INTERCONNECTORID = Column(
        ForeignKey("nemweb_meta.INTERCONNECTORID.id"), index=True
    )
    METEREDMWFLOW = Column(DECIMAL(10, 5))
    MWLOSSES = Column(DECIMAL(8, 5))
    EXPORTLIMIT = Column(DECIMAL(10, 5))
    IMPORTLIMIT = Column(DECIMAL(10, 5))
    MARGINALLOSS = Column(DECIMAL(6, 5))
    DISPATCHINTERVAL = Column(BIGINT(20), index=True)
    MWFLOW = Column(DECIMAL(10, 5))
    INTERVENTION = Column(
        TINYINT(4), nullable=False, index=True, server_default=text("0")
    )

    INTERCONNECTORID1 = relationship("INTERCONNECTORID")


class MTPASAINTERCONNECTORSOLUTION(Base):
    __tablename__ = "MTPASA_INTERCONNECTORSOLUTION"
    __table_args__ = (
        Index(
            "uniq",
            "RUN_DATETIME",
            "RUN_NO",
            "DAY",
            "INTERCONNECTORID",
            "RUNTYPE",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    RUN_DATETIME = Column(DateTime, index=True)
    RUN_NO = Column(INTEGER(11), index=True)
    RUNTYPE = Column(ForeignKey("RUNTYPE.ID"), index=True)
    DAY = Column(DateTime, index=True)
    INTERCONNECTORID = Column(
        ForeignKey("nemweb_meta.INTERCONNECTORID.id"), index=True
    )
    CAPACITYMWFLOW = Column(DECIMAL(12, 2))
    CALCULATEDEXPORTLIMIT = Column(DECIMAL(12, 2))
    CALCULATEDIMPORTLIMIT = Column(DECIMAL(12, 2))

    INTERCONNECTORID1 = relationship("INTERCONNECTORID")
    RUNTYPE1 = relationship("RUNTYPE")


class P5MININTERCONNECTORSOLN(Base):
    __tablename__ = "P5MIN_INTERCONNECTORSOLN"
    __table_args__ = (
        Index(
            "uniq",
            "RUN_DATETIME",
            "INTERCONNECTORID",
            "INTERVAL_DATETIME",
            unique=True,
        ),
    )

    ID = Column(INTEGER(11), primary_key=True)
    RUN_DATETIME = Column(DateTime, index=True)
    INTERCONNECTORID = Column(
        ForeignKey("nemweb_meta.INTERCONNECTORID.id"), index=True
    )
    INTERVAL_DATETIME = Column(DateTime, index=True)
    METEREDMWFLOW = Column(DECIMAL(10, 5))
    MWFLOW = Column(DECIMAL(10, 5))
    MWLOSSES = Column(DECIMAL(10, 5))
    EXPORTLIMIT = Column(DECIMAL(10, 5))
    IMPORTLIMIT = Column(DECIMAL(10, 5))
    MARGINALLOSS = Column(DECIMAL(6, 5))
    FCASEXPORTLIMIT = Column(DECIMAL(10, 5))
    FCASIMPORTLIMIT = Column(DECIMAL(10, 5))

    INTERCONNECTORID1 = relationship("INTERCONNECTORID")


class PREDISPATCHINTERCONNECTORSOLN(Base):
    __tablename__ = "PREDISPATCH_INTERCONNECTOR_SOLN"
    __table_args__ = (
        Index(
            "uniq",
            "INTERCONNECTORID",
            "DATETIME",
            "PREDISPATCHSEQNO",
            "INTERVENTION",
            unique=True,
        ),
    )

    id = Column(INTEGER(11), primary_key=True)
    PREDISPATCHSEQNO = Column(INTEGER(11), index=True)
    INTERCONNECTORID = Column(
        ForeignKey("nemweb_meta.INTERCONNECTORID.id"), index=True
    )
    PERIODID = Column(TINYINT(4), index=True)
    METEREDMWFLOW = Column(DECIMAL(10, 5))
    MWFLOW = Column(DECIMAL(10, 5))
    MWLOSSES = Column(DECIMAL(10, 5))
    DATETIME = Column(DateTime, index=True)
    EXPORTLIMIT = Column(DECIMAL(10, 5))
    IMPORTLIMIT = Column(DECIMAL(10, 5))
    MARGINALLOSS = Column(DECIMAL(6, 5), nullable=False)
    INTERVENTION = Column(TINYINT(4), nullable=False, index=True)

    INTERCONNECTORID1 = relationship("INTERCONNECTORID")


class TRADINGINTERCONNECTORRE(Base):
    __tablename__ = "TRADING_INTERCONNECTORRES"
    __table_args__ = (
        Index("uniq", "SETTLEMENTDATE", "INTERCONNECTORID", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    INTERCONNECTORID = Column(
        ForeignKey("nemweb_meta.INTERCONNECTORID.id"), index=True
    )
    METEREDMWFLOW = Column(DECIMAL(6, 2))
    MWFLOW = Column(DECIMAL(6, 2))
    MWLOSSES = Column(DECIMAL(6, 2))

    INTERCONNECTORID1 = relationship("INTERCONNECTORID")
