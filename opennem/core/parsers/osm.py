"""
OpenNEM Open Street Map Parser

"""
import logging
from typing import Dict

import osm2geojson

from opennem.utils.http import http

logger = logging.getLogger(__name__)

OSM_API_WAY_URI = "https://www.openstreetmap.org/api/0.6/way/{way_id}/full"


def get_osm_way_url(way_id: str) -> str:
    """ Returns an XML thing for an OSM way id"""
    return OSM_API_WAY_URI.format(way_id=way_id)


def get_osm_way(way_id: str) -> Dict:
    """ Returns the xml payload from the osm api"""
    way_url = get_osm_way_url(way_id)

    way_resp = http.get(way_url)

    if not way_resp.ok:
        logger.error("No way")
        raise Exception("Could not get way: {}".format(way_resp.status_code))

    way_resp_content = way_resp.text

    geojson = osm2geojson.xml2geojson(way_resp_content, filter_used_refs=False, log_level="INFO")

    if not isinstance(geojson, dict):
        raise Exception("Did not get a valid server response from OSM API")

    if not "type" in geojson:
        raise Exception("Did not get a valid server response from OSM API")

    if geojson["type"] != "FeatureCollection":
        raise Exception("Did not get a valid FeatureCollection from OSM API")

    return geojson
