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
                    facility.status_label,
                    facility.fueltech_label,
                ]
            )

    return records


if __name__ == "__main__":
    stations_csv_serialize()
