"""
Query sanity and get a list of each facility and unit and their emission factors and sources

"""

import csv

from opennem.cms.queries import get_unit_factors


def main():
    factors = get_unit_factors()

    # sort by station code
    factors = sorted(factors, key=lambda x: x["code"])

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
                "emissions_factor_co2",
                "emissions_factor_source",
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

                writer.writerow(
                    [
                        facility["code"],
                        facility["name"],
                        facility["network_id"],
                        facility["network_region"],
                        unit["code"],
                        unit["fueltech_id"],
                        unit["emissions_factor_co2"],
                        unit["emissions_factor_source"],
                    ]
                )


if __name__ == "__main__":
    main()
