from opennem.exporter.aws import write_to_s3
from opennem.exporter.geojson import stations_geojson_serialize
from opennem.exporter.local import write_to_local


def stations_geojson_to_s3():
    stations_geojson = stations_geojson_serialize()

    write_to_s3("geo/stations.json", stations_geojson)


def stations_geojson_to_local():
    stations_geojson = stations_geojson_serialize()

    write_to_local("stations.json", stations_geojson)


if __name__ == "__main__":
    stations_geojson_to_s3()
    stations_geojson_to_local()
