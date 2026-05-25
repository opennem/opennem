"""
Pollution data schemas and enums for NPI substances
"""

from enum import StrEnum


class DataQuality(StrEnum):
    """Data-quality indicators for NPI pollution measurements.

    Each value names the methodology used to derive a reported pollutant
    quantity, in descending order of confidence.

    Attributes:
        MEASURED: Direct measurement at the source.
        CALCULATED: Derived from engineering calculations.
        ESTIMATED: Estimated using published methods.
        EMISSION_FACTORS: Computed via standard emission factors.
        MASS_BALANCE: Inferred from mass-balance calculations.
        APPROVED_ALTERNATIVE: Reported via an EPA-approved alternative method.
        UNKNOWN: Methodology not specified by the reporting facility.
    """

    MEASURED = "measured"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    EMISSION_FACTORS = "emission_factors"
    MASS_BALANCE = "mass_balance"
    APPROVED_ALTERNATIVE = "approved_alternative"
    UNKNOWN = "unknown"


class PollutantCategory(StrEnum):
    """High-level groupings of NPI-tracked pollutants.

    Used to filter `/pollution/facilities` queries down to a class of
    substances. When no filter is supplied the API defaults to
    `air_pollutant`.

    Attributes:
        AIR_POLLUTANT: Combustion by-products and gases released to air
            (NOx, SOx, CO, PM10, PM2.5, VOCs, ammonia, HCl).
        WATER_POLLUTANT: Substances released to receiving waterways
            (e.g. fluoride compounds).
        HEAVY_METAL: Heavy-metal compounds (As, Cd, Cr, Cu, Hg, Ni, Pb, Zn).
        ORGANIC: Organic compounds and complex hydrocarbons (benzene,
            formaldehyde, PAH, dioxins).
    """

    AIR_POLLUTANT = "air_pollutant"
    WATER_POLLUTANT = "water_pollutant"
    HEAVY_METAL = "heavy_metal"
    ORGANIC = "organic"

    @classmethod
    def default(cls) -> "PollutantCategory":
        """Default category for API responses"""
        return cls.AIR_POLLUTANT


class PollutantCode(StrEnum):
    """National Pollutant Inventory (NPI) substance codes.

    Each value identifies a specific substance the NPI tracks for reporting
    facilities. Group membership is documented by `PollutantCategory`; use
    `pollutant_category=` on `/pollution/facilities` to filter by group, or
    `pollutant_code=` for a specific substance.

    Attributes:
        NOX: Oxides of nitrogen (NOx).
        SO2: Sulfur dioxide (SO2).
        CO: Carbon monoxide (CO).
        PM10: Particulate matter ≤10 µm.
        PM2_5: Fine particulate matter ≤2.5 µm.
        VOC: Total volatile organic compounds.
        AMMONIA: Ammonia (NH3).
        HCL: Hydrochloric acid (HCl).
        AS: Arsenic and compounds.
        CD: Cadmium and compounds.
        CR3: Chromium (III) compounds.
        CR6: Chromium (VI) compounds.
        CU: Copper and compounds.
        HG: Mercury and compounds.
        NI: Nickel and compounds.
        PB: Lead and compounds.
        ZN: Zinc and compounds.
        BENZENE: Benzene.
        FORMALDEHYDE: Formaldehyde.
        PAH: Polycyclic aromatic hydrocarbons (B[a]P equivalent).
        DIOXINS: Polychlorinated dioxins and furans (TEQ).
        FLUORIDE: Fluoride compounds (water pollutant).
    """

    # Air pollutants
    NOX = "nox"
    SO2 = "so2"
    CO = "co"
    PM10 = "pm10"
    PM2_5 = "pm2_5"
    VOC = "voc"
    AMMONIA = "ammonia"
    HCL = "hcl"

    # Heavy metals
    AS = "as"
    CD = "cd"
    CR3 = "cr3"
    CR6 = "cr6"
    CU = "cu"
    HG = "hg"
    NI = "ni"
    PB = "pb"
    ZN = "zn"

    # Organic compounds
    BENZENE = "benzene"
    FORMALDEHYDE = "formaldehyde"
    PAH = "pah"
    DIOXINS = "dioxins"

    # Other
    FLUORIDE = "fluoride"


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
