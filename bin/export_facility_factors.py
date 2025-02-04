"""
Query sanity and get a list of each facility and unit and their emission factors and sources

"""

import csv
from dataclasses import dataclass

from opennem.cms.queries import get_unit_factors


@dataclass
class V3UnitFactor:
    facility_code: str
    emissions_factor_co2: float
    emissions_factor_source: str
    y_generated_gwh: float


def read_v3_facility_factors():
    with open("data/v3_emission_factors.csv") as f:
        reader = csv.reader(f)
        return {
            row[0]: V3UnitFactor(
                facility_code=row[0], emissions_factor_co2=row[2], emissions_factor_source=row[3], y_generated_gwh=row[4]
            )
            for row in reader
        }


def main():
    factors = get_unit_factors()

    # sort by station code
    factors = sorted(factors, key=lambda x: x["code"])
    v3_factors = read_v3_facility_factors()

    # parse into a csv file as one row for each unit containing facility into
    with open("facility_factors.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "facility_code",
                "facility_name",
                "network_id",
                "network_region",
                "unit_code",
                "fueltech_id",
                "v3_emission_factor_co2",
                "v3_emission_factor_source",
                "emissions_factor_co2",
                "emissions_factor_source",
                "y_generated_gwh",
            ]
        )
        for facility in factors:
            for unit in facility["units"]:
                if unit["fueltech_id"] in [
                    "solar_utility",
                    "wind",
                    "battery",
                    "pumps",
                    "hydro",
                    "battery_charging",
                    "battery_discharging",
                ]:
                    continue

                v3_factor = v3_factors.get(unit["code"])

                writer.writerow(
                    [
                        facility["code"],
                        facility["name"],
                        facility["network_id"],
                        facility["network_region"],
                        unit["code"],
                        unit["fueltech_id"],
                        round(float(v3_factor.emissions_factor_co2), 4) if v3_factor and v3_factor.emissions_factor_co2 else None,
                        v3_factor.emissions_factor_source if v3_factor and v3_factor.emissions_factor_source else None,
                        unit["emissions_factor_co2"],
                        unit["emissions_factor_source"],
                        round(float(v3_factor.y_generated_gwh), 4) if v3_factor and v3_factor.y_generated_gwh else None,
                    ]
                )


if __name__ == "__main__":
    main()
