"""
NPI (National Pollutant Inventory) XML Parser

Parses NPI XML export files containing facility pollution data
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("opennem.parsers.npi")


@dataclass
class NPISubstance:
    """NPI substance/pollutant data"""

    name: str
    destination: str  # Air Total, Air Point, Air Fugitive, Water, Land
    quantity_kg: Decimal
    # Estimation methods
    mass_balance: bool = False
    engineering_calc: bool = False
    direct_measurement: bool = False
    emission_factors: bool = False
    approved_alternative: bool = False


@dataclass
class NPIFacilityReport:
    """NPI facility pollution report for a given year"""

    # Facility identification
    facility_name: str
    jurisdiction_facility_id: str
    registered_business_name: str
    abn: str | None = None
    acn: str | None = None

    # Report metadata
    report_year: int = 0
    data_start_date: datetime | None = None
    data_end_date: datetime | None = None
    first_published_date: datetime | None = None
    last_updated_date: datetime | None = None

    # Location
    site_address_street: str | None = None
    site_address_suburb: str | None = None
    site_address_state: str | None = None
    site_address_postcode: str | None = None
    site_latitude: float | None = None
    site_longitude: float | None = None

    # Activities
    main_activities: str | None = None
    anzsic_codes: list[dict[str, str]] = field(default_factory=list)

    # Additional facility data
    company_website: str | None = None
    number_of_employees: int | None = None
    sub_threshold: bool = False

    # Contact information (from public_contact)
    contact_name: str | None = None
    contact_surname: str | None = None
    contact_position: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None

    # Pollution data
    substances: list[NPISubstance] = field(default_factory=list)


def parse_boolean(value: str | None) -> bool:
    """Parse Y/N values to boolean"""
    if value is None:
        return False
    return value.upper() == "Y"


def parse_decimal(value: str | None) -> Decimal | None:
    """Parse decimal values from string"""
    if value is None or value == "":
        return None
    try:
        # Handle scientific notation and regular decimals
        return Decimal(value)
    except Exception as e:
        logger.warning(f"Could not parse decimal value '{value}': {e}")
        return None


def parse_date(value: str | None) -> datetime | None:
    """Parse date strings in YYYY-MM-DD format"""
    if value is None or value == "":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Could not parse date '{value}': {e}")
        return None


def parse_npi_xml(file_path: Path | str) -> list[NPIFacilityReport]:
    """
    Parse an NPI XML export file and return list of facility reports

    Args:
        file_path: Path to the XML file

    Returns:
        List of NPIFacilityReport objects
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"NPI XML file not found: {file_path}")

    logger.info(f"Parsing NPI XML file: {file_path}")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise

    reports = []

    # Find all report elements
    for report_elem in root.findall(".//report"):
        try:
            report = parse_facility_report(report_elem)
            if report:
                reports.append(report)
        except Exception as e:
            logger.error(f"Failed to parse report: {e}")
            continue

    logger.info(f"Parsed {len(reports)} facility reports from NPI XML")
    return reports


def parse_facility_report(report_elem: ET.Element) -> NPIFacilityReport | None:
    """Parse a single facility report element"""

    def get_text(elem_name: str) -> str | None:
        elem = report_elem.find(elem_name)
        return elem.text if elem is not None else None

    def get_float(elem_name: str) -> float | None:
        text = get_text(elem_name)
        if text:
            try:
                return float(text)
            except ValueError:
                logger.warning(f"Could not parse float from {elem_name}: {text}")
        return None

    def get_int(elem_name: str) -> int | None:
        text = get_text(elem_name)
        if text:
            try:
                return int(text)
            except ValueError:
                logger.warning(f"Could not parse int from {elem_name}: {text}")
        return None

    # Required fields
    facility_name = get_text("facility_name")
    jurisdiction_facility_id = get_text("jurisdiction_facility_id")
    registered_business_name = get_text("registered_business_name")

    # Only facility_name and jurisdiction_facility_id are truly required
    # registered_business_name is optional (missing in 1998 data)
    if not all([facility_name, jurisdiction_facility_id]):
        logger.warning("Missing required fields in facility report")
        return None

    report = NPIFacilityReport(
        facility_name=facility_name,
        jurisdiction_facility_id=jurisdiction_facility_id,
        registered_business_name=registered_business_name,
        abn=get_text("abn"),
        acn=get_text("acn"),
        report_year=get_int("year") or 0,
        data_start_date=parse_date(get_text("data_start_date")),
        data_end_date=parse_date(get_text("data_end_date")),
        first_published_date=parse_date(get_text("first_published_date")),
        last_updated_date=parse_date(get_text("last_updated_date")),
        site_address_street=get_text("site_address_street"),
        site_address_suburb=get_text("site_address_suburb"),
        site_address_state=get_text("site_address_state"),
        site_address_postcode=get_text("site_address_postcode"),
        site_latitude=get_float("site_latitude"),
        site_longitude=get_float("site_longitude"),
        main_activities=get_text("main_activities"),
        number_of_employees=get_int("number_of_employees"),
        sub_threshold=parse_boolean(get_text("sub_threshold")),
    )

    # Parse ANZSIC codes
    anzsic_elem = report_elem.find("anzsic_codes")
    if anzsic_elem is not None:
        for code_elem in anzsic_elem.findall("anzsic_code"):
            code_type = code_elem.findtext("type")
            code_value = code_elem.findtext("code")
            code_name = code_elem.findtext("name")
            if code_value:
                report.anzsic_codes.append({"type": code_type or "", "code": code_value, "name": code_name or ""})

    # Parse public contact information
    contact_elem = report_elem.find("public_contact")
    if contact_elem is not None:
        report.contact_name = contact_elem.findtext("name")
        report.contact_surname = contact_elem.findtext("surname")
        report.contact_position = contact_elem.findtext("position")
        report.contact_phone = contact_elem.findtext("phone")
        report.contact_email = contact_elem.findtext("email")
        report.company_website = contact_elem.findtext("web_address")

    # Parse emissions/pollution data
    emissions_elem = report_elem.find("emissions")
    if emissions_elem is not None:
        for emission_elem in emissions_elem.findall("emission"):
            substance_name = emission_elem.findtext("substance")
            destination = emission_elem.findtext("destination")
            quantity_text = emission_elem.findtext("quantity_in_kg")

            if not all([substance_name, destination, quantity_text]):
                continue

            quantity = parse_decimal(quantity_text)
            if quantity is None:
                continue

            substance = NPISubstance(
                name=substance_name,
                destination=destination,
                quantity_kg=quantity,
                mass_balance=parse_boolean(emission_elem.findtext("mass_balance_estimation")),
                engineering_calc=parse_boolean(emission_elem.findtext("engineering_calculations_estimation")),
                direct_measurement=parse_boolean(emission_elem.findtext("direct_measurement_estimation")),
                emission_factors=parse_boolean(emission_elem.findtext("emission_factors_estimation")),
                approved_alternative=parse_boolean(emission_elem.findtext("approved_alternative_estimation")),
            )

            report.substances.append(substance)

    return report


def get_unique_substances(reports: list[NPIFacilityReport]) -> set[str]:
    """
    Extract unique substance names from all reports

    Useful for understanding what pollutants are reported
    """
    substances = set()
    for report in reports:
        for substance in report.substances:
            substances.add(substance.name)
    return substances


def filter_reports_by_substance(reports: list[NPIFacilityReport], substance_names: list[str]) -> list[NPIFacilityReport]:
    """
    Filter reports to only include specified substances

    Args:
        reports: List of facility reports
        substance_names: List of substance names to keep

    Returns:
        Filtered list of reports with only specified substances
    """
    filtered_reports = []

    for report in reports:
        filtered_substances = [s for s in report.substances if s.name in substance_names]

        if filtered_substances:
            # Create a copy of the report with filtered substances
            filtered_report = NPIFacilityReport(
                facility_name=report.facility_name,
                jurisdiction_facility_id=report.jurisdiction_facility_id,
                registered_business_name=report.registered_business_name,
                abn=report.abn,
                acn=report.acn,
                report_year=report.report_year,
                data_start_date=report.data_start_date,
                data_end_date=report.data_end_date,
                first_published_date=report.first_published_date,
                last_updated_date=report.last_updated_date,
                site_address_street=report.site_address_street,
                site_address_suburb=report.site_address_suburb,
                site_address_state=report.site_address_state,
                site_address_postcode=report.site_address_postcode,
                site_latitude=report.site_latitude,
                site_longitude=report.site_longitude,
                main_activities=report.main_activities,
                anzsic_codes=report.anzsic_codes,
                substances=filtered_substances,
                number_of_employees=report.number_of_employees,
                sub_threshold=report.sub_threshold,
            )
            filtered_reports.append(filtered_report)

    return filtered_reports


# Key substances for power generation monitoring
KEY_SUBSTANCES = [
    # Greenhouse gases (not typically in NPI, but check)
    "Carbon dioxide",
    "Methane",
    "Nitrous oxide",
    # Air pollutants
    "Oxides of Nitrogen",
    "Sulfur dioxide",
    "Carbon monoxide",
    "Particulate Matter 10.0 um",
    "Particulate Matter 2.5 um",
    # Heavy metals
    "Mercury & compounds",
    "Lead & compounds",
    "Arsenic & compounds",
    "Cadmium & compounds",
    "Chromium (III) compounds",
    "Chromium (VI) compounds",
    "Nickel & compounds",
    # Other pollutants
    "Total Volatile Organic Compounds",
    "Polycyclic aromatic hydrocarbons (B[a]Peq)",
    "Benzene",
    "Formaldehyde",
]
