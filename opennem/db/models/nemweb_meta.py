from sqlalchemy import (
    DECIMAL,
    Column,
    Date,
    ForeignKey,
    Index,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.mysql import (
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


class CATEGORY(Base):
    __tablename__ = "CATEGORY"

    ID = Column(TINYINT(4), primary_key=True)
    CATEGORY = Column(String(10, "utf8_bin"), nullable=False, unique=True)


class CLASSIFICATION(Base):
    __tablename__ = "CLASSIFICATION"

    ID = Column(TINYINT(4), primary_key=True)
    CLASSIFICATION = Column(String(15, "utf8_bin"), unique=True)


t_CURRENT_REGISTER = Table(
    "CURRENT_REGISTER",
    metadata,
    Column("ID", SMALLINT(6), server_default=text("'0'")),
    Column("DUID", String(10)),
    Column("STATION_NAME", String(100)),
    Column("PARTICIPANT", String(80)),
    Column("CLASSIFICATION", String(15)),
    Column("CATEGORY", String(10)),
    Column("TECHNOLOGY_TYPE", String(60)),
    Column("FUEL_SOURCE", String(45)),
    Column("REGIONID", String(6)),
    Column("DISPATCH_TYPE", String(45)),
    Column("UNIT_NO", String(50)),
    Column("UNIT_SIZE", DECIMAL(7, 3)),
    Column("REG_CAP", DECIMAL(7, 3)),
    Column("MAX_CAP", DECIMAL(7, 3)),
    Column("MAX_ROC", DECIMAL(4, 0)),
    Column("DATE", Date),
)


t_CURRENT_REGISTER_DATE = Table(
    "CURRENT_REGISTER_DATE", metadata, Column("DATE", Date)
)


class DISPATCHTYPE(Base):
    __tablename__ = "DISPATCH_TYPE"

    ID = Column(TINYINT(4), primary_key=True)
    DISPATCH_TYPE = Column(String(45, "utf8_bin"), nullable=False, unique=True)


class DUID(Base):
    __tablename__ = "DUID"

    ID = Column(SMALLINT(6), primary_key=True)
    DUID = Column(VARCHAR(10), unique=True)


t_DUID_EFFICIENCY = Table(
    "DUID_EFFICIENCY",
    metadata,
    Column("DUID", SMALLINT(6)),
    Column("THERMAL_EFFICIENCY", DECIMAL(7, 4)),
)


class FUELCATEGORY(Base):
    __tablename__ = "FUEL_CATEGORY"

    ID = Column(TINYINT(4), primary_key=True, unique=True)
    FUEL_CATEGORY = Column(String(45, "utf8_bin"))


class FUELTECH(Base):
    __tablename__ = "FUEL_TECHS"

    ID = Column(TINYINT(4), primary_key=True)
    FUEL_TECH = Column(String(45, "utf8_bin"), unique=True)
    openNEM_keys = Column(String(45, "utf8_bin"), unique=True)
    openNEM_colors = Column(String(7, "utf8_bin"))


t_FULL_REGISTER = Table(
    "FULL_REGISTER",
    metadata,
    Column("ID", SMALLINT(6), server_default=text("'0'")),
    Column("DUID", String(10)),
    Column("STATION_NAME", String(100)),
    Column("PARTICIPANT", String(80)),
    Column("CLASSIFICATION", String(15)),
    Column("CATEGORY", String(10)),
    Column("DISPATCH_TYPE", String(45)),
    Column("REGIONID", String(6)),
    Column("FUEL_CATEGORY", String(45)),
    Column("TECHNOLOGY_CATEGORY", String(45)),
    Column("FUEL_TECH", String(45)),
    Column("UNIT_NO", String(50)),
    Column("UNIT_SIZE", DECIMAL(7, 3)),
    Column("REG_CAP", DECIMAL(7, 3)),
    Column("MAX_CAP", DECIMAL(7, 3)),
    Column("MAX_ROC", DECIMAL(4, 0)),
    Column("DATE", Date),
)


t_GENERATOR_TECHNICAL_DATA = Table(
    "GENERATOR_TECHNICAL_DATA",
    metadata,
    Column("STATION_NAME_ID", SMALLINT(6)),
    Column("STATION_NAME", String(100)),
    Column("REGIONID", String(6)),
    Column("FUEL_TECH", String(45)),
    Column("CAPACITY", DECIMAL(29, 3)),
    Column("THERMAL_EFFICIENCY", DECIMAL(7, 4)),
    Column("SCOPE_1", DECIMAL(5, 4)),
)


t_LAST_REGISTERED_DATE = Table(
    "LAST_REGISTERED_DATE",
    metadata,
    Column("DUID", SMALLINT(6)),
    Column("LAST_DATE", Date),
)


t_NEM_EMISSION_INTENSITY = Table(
    "NEM_EMISSION_INTENSITY",
    metadata,
    Column("ID", SMALLINT(6), server_default=text("'0'")),
    Column("STATION_NAME", String(100)),
    Column("SCOPE_1", DECIMAL(5, 4)),
    Column("SCOPE_3", DECIMAL(5, 4)),
    Column("TOTAL", DECIMAL(6, 4)),
)


class PARTICIPANT(Base):
    __tablename__ = "PARTICIPANTS"

    ID = Column(SMALLINT(6), primary_key=True)
    PARTICIPANT = Column(String(80, "utf8_bin"), unique=True)


class REGIONID(Base):
    __tablename__ = "REGIONID"

    id = Column(TINYINT(4), primary_key=True)
    REGIONID = Column(VARCHAR(6), unique=True)


t_REGION_SUMMARY = Table(
    "REGION_SUMMARY",
    metadata,
    Column("REGIONID", String(6)),
    Column("FUEL_TECH", String(45)),
    Column("MW", DECIMAL(29, 3)),
)


t_REGISTERED_GENERATORS = Table(
    "REGISTERED_GENERATORS",
    metadata,
    Column("STATION_NAME", String(100)),
    Column("MW", DECIMAL(29, 3)),
)


t_STANDARDISED_REGISTER = Table(
    "STANDARDISED_REGISTER",
    metadata,
    Column("id", SMALLINT(6), server_default=text("'0'")),
    Column("DUID", String(10)),
    Column("STATION_NAME", String(100)),
    Column("PARTICIPANT", String(80)),
    Column("CLASSIFICATION", String(15)),
    Column("CATEGORY", String(10)),
    Column("DISPATCH_TYPE", String(45)),
    Column("REGIONID", String(6)),
    Column("FUEL_CATEGORY", String(45)),
    Column("TECHNOLOGY_CATEGORY", String(45)),
    Column("FUEL_TECH", String(45)),
    Column("UNIT_NO", String(50)),
    Column("UNIT_SIZE", DECIMAL(7, 3)),
    Column("REG_CAP", DECIMAL(7, 3)),
    Column("MAX_CAP", DECIMAL(7, 3)),
    Column("MAX_ROC", DECIMAL(4, 0)),
    Column("DATE", Date),
)


class STATIONNAME(Base):
    __tablename__ = "STATION_NAMES"

    ID = Column(SMALLINT(6), primary_key=True)
    STATION_NAME = Column(String(100, "utf8_bin"), unique=True)


t_STATION_SUMMARY = Table(
    "STATION_SUMMARY",
    metadata,
    Column("ID", SMALLINT(6), server_default=text("'0'")),
    Column("DUID", String(10)),
    Column("STATION_NAME_ID", SMALLINT(6), server_default=text("'0'")),
    Column("STATION_NAME", String(100)),
    Column("PARTICIPANT", String(80)),
    Column("REGIONID", String(6)),
    Column("openNEM_keys", String(45)),
    Column("openNEM_colors", String(7)),
    Column("REG_CAP", DECIMAL(7, 3)),
    Column("MAX_CAP", DECIMAL(7, 3)),
    Column("MAX_ROC", DECIMAL(4, 0)),
)


class TECHNOLOGYCATEGORY(Base):
    __tablename__ = "TECHNOLOGY_CATEGORY"

    ID = Column(TINYINT(4), primary_key=True)
    TECHNOLOGY_CATEGORY = Column(String(45, "utf8_bin"), unique=True)


t__MAPPING_FUEL_SOURCE = Table(
    "_MAPPING_FUEL_SOURCE",
    metadata,
    Column("ID", TINYINT(4), server_default=text("'0'")),
    Column("FUEL_SOURCE", String(45)),
    Column("FUEL_CATEGORY", String(45)),
)


t__MAPPING_TECHNOLOGY_TYPE = Table(
    "_MAPPING_TECHNOLOGY_TYPE",
    metadata,
    Column("ID", TINYINT(4), server_default=text("'0'")),
    Column("TECHNOLOGY_TYPE", String(60)),
    Column("TECHNOLOGY_CATEGORY", String(45)),
)


t__MAPPING_TECH_FUEL = Table(
    "_MAPPING_TECH_FUEL",
    metadata,
    Column("FUEL_TECH", String(45)),
    Column("FUEL_CATEGORY", String(45)),
    Column("TECHNOLOGY_CATEGORY", String(45)),
)


class FUELSOURCE(Base):
    __tablename__ = "FUEL_SOURCES"

    ID = Column(TINYINT(4), primary_key=True)
    FUEL_SOURCE = Column(String(45, "utf8_bin"), unique=True)
    FUEL_CATEGORY_ID = Column(ForeignKey("FUEL_CATEGORY.ID"), index=True)

    FUEL_CATEGORY = relationship("FUELCATEGORY")


class FUELTECHMAPPING(Base):
    __tablename__ = "FUEL_TECH_MAPPING"

    ID = Column(TINYINT(4), primary_key=True)
    FUEL_CATEGORY_ID = Column(ForeignKey("FUEL_CATEGORY.ID"), index=True)
    TECHNOLOGY_CATEGORY_ID = Column(
        ForeignKey("TECHNOLOGY_CATEGORY.ID"), index=True
    )
    FUEL_TECH_ID = Column(ForeignKey("FUEL_TECHS.ID"), index=True)

    FUEL_CATEGORY = relationship("FUELCATEGORY")
    FUEL_TECH = relationship("FUELTECH")
    TECHNOLOGY_CATEGORY = relationship("TECHNOLOGYCATEGORY")


class INTERCONNECTORID(Base):
    __tablename__ = "INTERCONNECTORID"

    id = Column(TINYINT(4), primary_key=True)
    INTERCONNECTORID = Column(VARCHAR(9), nullable=False, unique=True)
    FROM_REGIONID = Column(ForeignKey("REGIONID.id"), index=True)
    TO_REGIONID = Column(ForeignKey("REGIONID.id"), index=True)

    REGIONID = relationship(
        "REGIONID", primaryjoin="INTERCONNECTORID.FROM_REGIONID == REGIONID.id"
    )
    REGIONID1 = relationship(
        "REGIONID", primaryjoin="INTERCONNECTORID.TO_REGIONID == REGIONID.id"
    )


class NTNDPEMISSION(Base):
    __tablename__ = "NTNDP_EMISSIONS"

    ID = Column(INTEGER(11), primary_key=True)
    NTNDP_STATION_NAME = Column(String(45, "utf8_bin"), unique=True)
    STATION_NAME_ID = Column(ForeignKey("STATION_NAMES.ID"), unique=True)
    SCOPE_1 = Column(DECIMAL(5, 4))
    SCOPE_3 = Column(DECIMAL(5, 4))

    STATION_NAME = relationship("STATIONNAME")


class NTNDPTECHNICALDATUM(Base):
    __tablename__ = "NTNDP_TECHNICAL_DATA"

    ID = Column(INTEGER(11), primary_key=True)
    UNIT = Column(String(45, "utf8_bin"))
    DUID = Column(ForeignKey("DUID.ID"), index=True)
    FIRST_RUN = Column(SMALLINT(6))
    AUX_LOAD = Column(TINYINT(4))
    HOT_DAY_DERATE = Column(DECIMAL(4, 2))
    ROCUP_START = Column(SMALLINT(6))
    ROCUP_NORM = Column(SMALLINT(6))
    ROCDOWN_START = Column(SMALLINT(6))
    ROCDOWN_NORM = Column(MEDIUMINT(9))
    THERMAL_EFFICIENCY = Column(TINYINT(4))

    DUID1 = relationship("DUID")


t_RET_BASELINE = Table(
    "RET_BASELINE",
    metadata,
    Column("ID", ForeignKey("DUID.ID"), nullable=False, index=True),
    Column("BASELINE", INTEGER(11), nullable=False),
)


class TECHNOLOGYTYPE(Base):
    __tablename__ = "TECHNOLOGY_TYPES"

    ID = Column(TINYINT(4), primary_key=True)
    TECHNOLOGY_TYPE = Column(String(60, "utf8_bin"), unique=True)
    TECHNOLOGY_CATEGORY_ID = Column(
        ForeignKey("TECHNOLOGY_CATEGORY.ID"), index=True
    )

    TECHNOLOGY_CATEGORY = relationship("TECHNOLOGYCATEGORY")


class REGISTER(Base):
    __tablename__ = "REGISTER"
    __table_args__ = (
        Index("uniq", "DATE", "DUID", "UNIT_SIZE", "UNIT_NO", unique=True),
    )

    ID = Column(INTEGER(11), primary_key=True, unique=True)
    DUID = Column(ForeignKey("DUID.ID"), nullable=False, index=True)
    PARTICIPANT_ID = Column(
        ForeignKey("PARTICIPANTS.ID"), nullable=False, index=True
    )
    STATION_NAME_ID = Column(
        ForeignKey("STATION_NAMES.ID"), nullable=False, index=True
    )
    REGIONID = Column(ForeignKey("REGIONID.id"), nullable=False, index=True)
    DISPATCH_TYPE_ID = Column(
        ForeignKey("DISPATCH_TYPE.ID"), nullable=False, index=True
    )
    CATEGORY_ID = Column(ForeignKey("CATEGORY.ID"), nullable=False, index=True)
    CLASSIFICATION_ID = Column(
        ForeignKey("CLASSIFICATION.ID"), nullable=False, index=True
    )
    FUEL_SOURCE_ID = Column(
        ForeignKey("FUEL_SOURCES.ID"), nullable=False, index=True
    )
    TECHNOLOGY_TYPE_ID = Column(
        ForeignKey("TECHNOLOGY_TYPES.ID"), nullable=False, index=True
    )
    UNIT_NO = Column(VARCHAR(50))
    UNIT_SIZE = Column(DECIMAL(7, 3))
    MAX_CAP = Column(DECIMAL(7, 3))
    REG_CAP = Column(DECIMAL(7, 3))
    MAX_ROC = Column(DECIMAL(4, 0))
    DATE = Column(Date, nullable=False, index=True)

    CATEGORY = relationship("CATEGORY")
    CLASSIFICATION = relationship("CLASSIFICATION")
    DISPATCH_TYPE = relationship("DISPATCHTYPE")
    DUID1 = relationship("DUID")
    FUEL_SOURCE = relationship("FUELSOURCE")
    PARTICIPANT = relationship("PARTICIPANT")
    REGIONID1 = relationship("REGIONID")
    STATION_NAME = relationship("STATIONNAME")
    TECHNOLOGY_TYPE = relationship("TECHNOLOGYTYPE")
