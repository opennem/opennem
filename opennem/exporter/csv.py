import csv

from opennem.api.stations import get_stations


def stations_csv_serialize():
    stations = get_stations()

    records = []

    for station in stations:
        for facility in station.facilities:
            records.append(
                [
                    station.oid,
                    station.ocode,
                    station.name,
                    facility.network_code,
                    facility.network_region,
                    facility.status.label if facility.status else None,
                    facility.fueltech.label if facility.fueltech else None,
                ]
            )

    return records


if __name__ == "__main__":
    stations_csv_serialize()
