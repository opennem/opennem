import csv

from opennem.api.stations import get_stations


def stations_csv_serialize():
    stations = get_stations()

    records = []

    for station in stations:
        for facility in station.facilities:
            rec = {
                "oid": station.oid,
                "ocode": station.ocode,
                "name": station.name,
                "network": facility.network_code,
                "region": facility.network_region,
                "status": facility.status_label,
                "fueltech": facility.fueltech_label,
                "added_by": facility.created_by,
                "updated_by": facility.created_by,
            }
            records.append(rec)

    return records


if __name__ == "__main__":
    stations_csv_serialize()
