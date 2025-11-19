"""
Pollution data schemas and enums for NPI substances
"""

from enum import Enum


class DataQuality(str, Enum):
    """Data quality indicators for pollution measurements"""

    MEASURED = "measured"  # Direct measurement
    CALCULATED = "calculated"  # Engineering calculations
    ESTIMATED = "estimated"  # Estimation methods
    EMISSION_FACTORS = "emission_factors"  # Using emission factors
    MASS_BALANCE = "mass_balance"  # Mass balance calculations
    APPROVED_ALTERNATIVE = "approved_alternative"  # EPA-approved alternative method
    UNKNOWN = "unknown"  # Quality not specified


class PollutantCategory(str, Enum):
    """Categories of pollutants tracked in NPI data"""

    AIR_POLLUTANT = "air_pollutant"
    WATER_POLLUTANT = "water_pollutant"
    HEAVY_METAL = "heavy_metal"
    ORGANIC = "organic"

    @classmethod
    def default(cls) -> PollutantCategory:
        """Default category for API responses"""
        return cls.AIR_POLLUTANT


class PollutantCode(str, Enum):
    """Pollutant substance codes used in the database"""

    # Air pollutants
    NOX = "nox"  # Oxides of Nitrogen
    SO2 = "so2"  # Sulfur dioxide
    CO = "co"  # Carbon monoxide
    PM10 = "pm10"  # Particulate Matter 10.0 um
    PM2_5 = "pm2_5"  # Particulate Matter 2.5 um
    VOC = "voc"  # Total Volatile Organic Compounds
    AMMONIA = "ammonia"  # Ammonia
    HCL = "hcl"  # Hydrochloric acid

    # Heavy metals
    AS = "as"  # Arsenic & compounds
    CD = "cd"  # Cadmium & compounds
    CR3 = "cr3"  # Chromium (III) compounds
    CR6 = "cr6"  # Chromium (VI) compounds
    CU = "cu"  # Copper & compounds
    HG = "hg"  # Mercury & compounds
    NI = "ni"  # Nickel & compounds
    PB = "pb"  # Lead & compounds
    ZN = "zn"  # Zinc & compounds

    # Organic compounds
    BENZENE = "benzene"  # Benzene
    FORMALDEHYDE = "formaldehyde"  # Formaldehyde
    PAH = "pah"  # Polycyclic aromatic hydrocarbons
    DIOXINS = "dioxins"  # Polychlorinated dioxins and furans

    # Other
    FLUORIDE = "fluoride"  # Fluoride compounds


# Mapping of pollutant codes to their categories
POLLUTANT_CATEGORIES = {
    # Air pollutants
    PollutantCode.NOX: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.SO2: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.CO: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.PM10: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.PM2_5: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.VOC: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.AMMONIA: PollutantCategory.AIR_POLLUTANT,
    PollutantCode.HCL: PollutantCategory.AIR_POLLUTANT,
    # Heavy metals
    PollutantCode.AS: PollutantCategory.HEAVY_METAL,
    PollutantCode.CD: PollutantCategory.HEAVY_METAL,
    PollutantCode.CR3: PollutantCategory.HEAVY_METAL,
    PollutantCode.CR6: PollutantCategory.HEAVY_METAL,
    PollutantCode.CU: PollutantCategory.HEAVY_METAL,
    PollutantCode.HG: PollutantCategory.HEAVY_METAL,
    PollutantCode.NI: PollutantCategory.HEAVY_METAL,
    PollutantCode.PB: PollutantCategory.HEAVY_METAL,
    PollutantCode.ZN: PollutantCategory.HEAVY_METAL,
    # Organic compounds
    PollutantCode.BENZENE: PollutantCategory.ORGANIC,
    PollutantCode.FORMALDEHYDE: PollutantCategory.ORGANIC,
    PollutantCode.PAH: PollutantCategory.ORGANIC,
    PollutantCode.DIOXINS: PollutantCategory.ORGANIC,
    # Other
    PollutantCode.FLUORIDE: PollutantCategory.WATER_POLLUTANT,
}


def get_pollutant_category(code: str | PollutantCode) -> PollutantCategory:
    """Get the category for a pollutant code"""
    if isinstance(code, str):
        try:
            code = PollutantCode(code)
        except ValueError:
            return PollutantCategory.AIR_POLLUTANT  # Default for unknown
    return POLLUTANT_CATEGORIES.get(code, PollutantCategory.AIR_POLLUTANT)


def get_pollutants_by_category(category: PollutantCategory) -> list[PollutantCode]:
    """Get all pollutant codes for a given category"""
    return [code for code, cat in POLLUTANT_CATEGORIES.items() if cat == category]


# Pollutant labels (full English names)
POLLUTANT_LABELS = {
    # Air pollutants
    PollutantCode.NOX: "Oxides of Nitrogen",
    PollutantCode.SO2: "Sulfur dioxide",
    PollutantCode.CO: "Carbon monoxide",
    PollutantCode.PM10: "Particulate Matter 10.0 μm",
    PollutantCode.PM2_5: "Particulate Matter 2.5 μm",
    PollutantCode.VOC: "Total Volatile Organic Compounds",
    PollutantCode.AMMONIA: "Ammonia",
    PollutantCode.HCL: "Hydrochloric acid",
    # Heavy metals
    PollutantCode.AS: "Arsenic & compounds",
    PollutantCode.CD: "Cadmium & compounds",
    PollutantCode.CR3: "Chromium (III) compounds",
    PollutantCode.CR6: "Chromium (VI) compounds",
    PollutantCode.CU: "Copper & compounds",
    PollutantCode.HG: "Mercury & compounds",
    PollutantCode.NI: "Nickel & compounds",
    PollutantCode.PB: "Lead & compounds",
    PollutantCode.ZN: "Zinc & compounds",
    # Organic compounds
    PollutantCode.BENZENE: "Benzene",
    PollutantCode.FORMALDEHYDE: "Formaldehyde",
    PollutantCode.PAH: "Polycyclic aromatic hydrocarbons (B[a]P equivalent)",
    PollutantCode.DIOXINS: "Polychlorinated dioxins and furans (TEQ)",
    # Other
    PollutantCode.FLUORIDE: "Fluoride compounds",
}


def get_pollutant_label(code: str | PollutantCode) -> str:
    """Get the full English label for a pollutant code"""
    if isinstance(code, str):
        try:
            code = PollutantCode(code)
        except ValueError:
            return code  # Return the code itself if unknown
    return POLLUTANT_LABELS.get(code, code.value)
