"""
OpenNEM Open Street Map Parser

Handles fetching geometry from OSM for both ways (positive IDs) and relations (negative IDs).
"""

import logging

import osm2geojson
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from opennem.utils.http import http

logger = logging.getLogger(__name__)

OSM_API_WAY_URI = "https://www.openstreetmap.org/api/0.6/way/{way_id}/full"
OSM_API_RELATION_URI = "https://www.openstreetmap.org/api/0.6/relation/{relation_id}/full"

VALID_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}


def get_osm_url(osm_id: str) -> str:
    """Returns the OSM API URL for a way (positive) or relation (negative) ID"""
    osm_id_int = int(osm_id)
    if osm_id_int < 0:
        return OSM_API_RELATION_URI.format(relation_id=abs(osm_id_int))
    return OSM_API_WAY_URI.format(way_id=osm_id)


def get_osm_way_url(way_id: str) -> str:
    """Returns an XML thing for an OSM way id"""
    return OSM_API_WAY_URI.format(way_id=way_id)


async def get_osm_features(osm_id: str) -> dict:
    """Fetch GeoJSON FeatureCollection from OSM API for a way or relation ID"""
    url = get_osm_url(osm_id)

    resp = await http.get(url)

    if not resp.is_success:
        raise Exception(f"OSM API error for {osm_id}: {resp.status_code}")

    geojson_response = osm2geojson.xml2geojson(resp.text, filter_used_refs=False, log_level="INFO")

    if not isinstance(geojson_response, dict):
        raise Exception("Did not get a valid server response from OSM API")

    if geojson_response.get("type") != "FeatureCollection":
        raise Exception("Did not get a valid FeatureCollection from OSM API")

    if "features" not in geojson_response:
        raise Exception("GeoJSON has no features")

    return geojson_response


async def get_osm_way(way_id: str) -> dict:
    """Returns the GeoJSON FeatureCollection from the OSM API (legacy wrapper)"""
    return await get_osm_features(way_id)


def _find_polygon(geojson: dict) -> dict | None:
    for feature in geojson["features"]:
        if feature["geometry"]["type"] in VALID_GEOMETRY_TYPES:
            return feature["geometry"]
    return None


async def get_osm_geom(way_id: str, srid: int = 4326) -> WKBElement:
    """Returns a WKB element from an OSM way/relation ID.

    Handles both Polygon and MultiPolygon geometries.

    The sign convention (negative means relation) is not reliable in stored data: most
    large wind and solar farms are mapped as relations, and their ids are held unsigned,
    so a way lookup either 404/410s or resolves to an unrelated line with no closed area.
    When the id read as a way yields nothing usable, retry it as a relation before giving
    up — that recovers the majority of failures without needing every id re-signed.
    """
    osm_id_int = int(way_id)
    attempts: list[str] = [way_id]
    if osm_id_int > 0:
        attempts.append(str(-osm_id_int))

    last_error: Exception | None = None
    for candidate in attempts:
        try:
            geojson = await get_osm_features(candidate)
        except Exception as exc:  # noqa: BLE001 - try the other object type before failing
            last_error = exc
            continue

        geom_dict = _find_polygon(geojson)
        if geom_dict:
            if candidate != way_id:
                logger.info(f"OSM id {way_id} resolved as a relation, not a way")
            return from_shape(shape(geom_dict), srid=srid)

        last_error = Exception(f"No polygon/multipolygon found for OSM ID {candidate}")

    raise last_error or Exception(f"No geometry found for OSM ID {way_id}")
