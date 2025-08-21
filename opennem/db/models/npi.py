"""
NPI (National Pollutant Inventory) Database Models

Models for storing pollution data from the Australian NPI
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from opennem.db.models.opennem import Base, BaseModel


class NPISubstance(Base, BaseModel):
    """
    Lookup table for substances/pollutants we track from NPI
    """

    __tablename__ = "npi_substances"

    code = Column(String(50), primary_key=True, nullable=False)
    npi_name = Column(Text, nullable=False, unique=True)
    cas_number = Column(String(50), nullable=True)
    category = Column(String(50), nullable=False)  # 'greenhouse', 'air_pollutant', 'water_pollutant', 'heavy_metal'
    unit = Column(String(10), default="kg")
    enabled = Column(Boolean, default=True)

    # Relationships
    pollution_records = relationship("NPIPollution", back_populates="substance")

    def __repr__(self) -> str:
        return f"<NPISubstance {self.code}: {self.npi_name}>"


class NPIFacility(Base, BaseModel):
    """
    NPI facility data - stores facility information from NPI reports
    """

    __tablename__ = "npi_facilities"

    # Use npi_id as primary key since it's unique
    npi_id = Column(String(50), primary_key=True, nullable=False)  # jurisdiction_facility_id from NPI
    npi_name = Column(Text, nullable=False)
    registered_business_name = Column(Text, nullable=True)
    abn = Column(String(20), nullable=True)
    acn = Column(String(20), nullable=True)

    # Location data
    site_latitude = Column(Numeric(10, 6), nullable=True)
    site_longitude = Column(Numeric(10, 6), nullable=True)
    location_state = Column(String(3), nullable=True)  # State abbreviation (NSW, VIC, QLD, etc.)
    site_address_suburb = Column(Text, nullable=True)
    site_address_postcode = Column(String(10), nullable=True)

    # Additional facility data
    company_website = Column(Text, nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    main_activities = Column(Text, nullable=True)

    # Report metadata
    report_year = Column(Integer, nullable=False)
    data_start_date = Column(DateTime(timezone=True), nullable=True)
    data_end_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    pollution_records = relationship("NPIPollution", back_populates="npi_facility")

    # Indexes
    __table_args__ = (
        Index("idx_npi_facilities_state", "location_state"),
        Index("idx_npi_facilities_year", "report_year"),
    )

    def __repr__(self) -> str:
        return f"<NPIFacility {self.npi_id}: {self.npi_name}>"


class NPIPollution(Base, BaseModel):
    """
    Pollution data from NPI reports
    """

    __tablename__ = "npi_pollution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    npi_facility_id = Column(String(50), ForeignKey("npi_facilities.npi_id"), nullable=False)
    substance_code = Column(String(50), ForeignKey("npi_substances.code"), nullable=False)
    report_year = Column(Integer, nullable=False)
    pollution_category = Column(String(20), nullable=False)  # 'air', 'water', 'land'
    pollution_subcategory = Column(String(20), nullable=True)  # 'point', 'fugitive', 'total'
    pollution_value = Column(Numeric(20, 6), nullable=False)
    pollution_unit = Column(String(10), default="kg")
    data_quality = Column(String(50), nullable=True)  # 'measured', 'calculated', 'estimated', 'emission_factors'

    # Relationships
    npi_facility = relationship("NPIFacility", back_populates="pollution_records")
    substance = relationship("NPISubstance", back_populates="pollution_records")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "npi_facility_id",
            "substance_code",
            "report_year",
            "pollution_category",
            "pollution_subcategory",
            name="uq_npi_pollution_facility_substance_year_category",
        ),
        Index("idx_npi_pollution_facility_year", "npi_facility_id", "report_year"),
        Index("idx_npi_pollution_substance", "substance_code"),
        Index("idx_npi_pollution_year", "report_year"),
    )

    def __repr__(self) -> str:
        return f"<NPIPollution {self.npi_facility_id} {self.substance_code} {self.report_year}>"


# Initial substances data for seeding
INITIAL_SUBSTANCES = [
    # Greenhouse gases (Note: CO2 typically not in NPI)
    {"code": "co2", "npi_name": "Carbon dioxide", "cas_number": "124-38-9", "category": "greenhouse"},
    {"code": "ch4", "npi_name": "Methane", "cas_number": "74-82-8", "category": "greenhouse"},
    {"code": "n2o", "npi_name": "Nitrous oxide", "cas_number": "10024-97-2", "category": "greenhouse"},
    # Air pollutants
    {"code": "nox", "npi_name": "Oxides of Nitrogen", "cas_number": None, "category": "air_pollutant"},
    {"code": "so2", "npi_name": "Sulfur dioxide", "cas_number": "7446-09-5", "category": "air_pollutant"},
    {"code": "co", "npi_name": "Carbon monoxide", "cas_number": "630-08-0", "category": "air_pollutant"},
    {"code": "pm10", "npi_name": "Particulate Matter 10.0 um", "cas_number": None, "category": "air_pollutant"},
    {"code": "pm2_5", "npi_name": "Particulate Matter 2.5 um", "cas_number": None, "category": "air_pollutant"},
    {"code": "voc", "npi_name": "Total Volatile Organic Compounds", "cas_number": None, "category": "air_pollutant"},
    # Heavy metals
    {"code": "hg", "npi_name": "Mercury & compounds", "cas_number": "7439-97-6", "category": "heavy_metal"},
    {"code": "pb", "npi_name": "Lead & compounds", "cas_number": "7439-92-1", "category": "heavy_metal"},
    {"code": "as", "npi_name": "Arsenic & compounds", "cas_number": "7440-38-2", "category": "heavy_metal"},
    {"code": "cd", "npi_name": "Cadmium & compounds", "cas_number": "7440-43-9", "category": "heavy_metal"},
    {"code": "cr3", "npi_name": "Chromium (III) compounds", "cas_number": None, "category": "heavy_metal"},
    {"code": "cr6", "npi_name": "Chromium (VI) compounds", "cas_number": None, "category": "heavy_metal"},
    {"code": "ni", "npi_name": "Nickel & compounds", "cas_number": "7440-02-0", "category": "heavy_metal"},
    {"code": "cu", "npi_name": "Copper & compounds", "cas_number": "7440-50-8", "category": "heavy_metal"},
    {"code": "zn", "npi_name": "Zinc & compounds", "cas_number": "7440-66-6", "category": "heavy_metal"},
    # Other pollutants
    {"code": "pah", "npi_name": "Polycyclic aromatic hydrocarbons (B[a]Peq)", "cas_number": None, "category": "air_pollutant"},
    {"code": "benzene", "npi_name": "Benzene", "cas_number": "71-43-2", "category": "air_pollutant"},
    {"code": "formaldehyde", "npi_name": "Formaldehyde", "cas_number": "50-00-0", "category": "air_pollutant"},
    {"code": "dioxins", "npi_name": "Polychlorinated dioxins and furans (TEQ)", "cas_number": None, "category": "air_pollutant"},
    {"code": "ammonia", "npi_name": "Ammonia", "cas_number": "7664-41-7", "category": "air_pollutant"},
    {"code": "hcl", "npi_name": "Hydrochloric acid", "cas_number": "7647-01-0", "category": "air_pollutant"},
    {"code": "fluoride", "npi_name": "Fluoride compounds", "cas_number": None, "category": "air_pollutant"},
]
