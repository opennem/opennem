from opennem.core.loader import load_data

from .mms import run_import_mms


def run_import_opennem_registry():
    station_fixture = load_data("facility_registry.json", from_fixture=True)
    mms = run_import_mms()

    nem_stations = {
        i: v
        for i, v in station_fixture.items()
        if v["location"]["state"] not in ["WA"]
    }

    for station_key, station_record in nem_stations.items():
        if not station_key in mms:
            print("Got {} which is not in registry".format(station_key))


if __name__ == "__main__":
    run_import_opennem_registry()
