"""

Google Places API

Methods to use and access the Google Places API

    * encode place names to geolocation using Google Places API
    * find a place id
    * autocomplete

"""
import logging
import os
import sys
import time
from datetime import timedelta

import requests
import requests_cache

from opennem.settings import scrapy_settings

logging.basicConfig(level=logging.INFO)


requests_cache.install_cache(
    scrapy_settings.requests_cache_path, expire_after=timedelta(days=60)
)

BACKOFF_TIME = 30
QUERY_LIMIT = 0


def google_geocode(
    query, region=None, api_key=None, return_full_response=False
):

    GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    query_params = {}

    query_components = {}

    url_params = {
        "key": scrapy_settings.google_places_api_key,
    }

    if region:
        query_params["region"] = region

    if "postal_code" in query:
        query_components["postal_code"] = query["postal_code"]

    if "country" in query:
        query_params["region"] = query["country"]
        query_components["country"] = query["country"]
        query.pop("country", None)

    url_params["components"] = "|".join(
        f"{k}:{v}" for k, v in query_components.items()
    )

    results = requests.get(GOOGLE_PLACES_URL, params=url_params).json()

    logging.debug(results)

    if not "status" in results:
        raise Exception("Invalid response")

    if results["status"] == "REQUEST_DENIED":
        raise Exception("API Key or other request denied error")

    if results["status"] == "OVER_QUERY_LIMIT":
        logging.warn("Hit Query Limit! Backing off for a bit.")
        time.sleep(5)  # sleep for 30 minutes
        return google_geocode(query, region, api_key, return_full_response)

    if results["status"] == "ZERO_RESULTS":
        return None

    if not results["status"] == "OK":
        logging.error("Error results for %s", query)
        raise Exception("No results: {}".format(results["status"]))

    if len(results["results"]) == 0:
        logging.error("No results for %s", query)
        return None

    cand = results["results"][0]
    return cand


def lookup_placeid(place_id, api_key=None, retry=0):

    GOOGLE_PLACES_URL = (
        "https://maps.googleapis.com/maps/api/place/details/json"
    )

    url_params = {
        "key": scrapy_settings.google_places_api_key,
        "place_id": place_id,
    }

    results = requests.get(GOOGLE_PLACES_URL, params=url_params).json()

    if not "status" in results:
        raise Exception("Invalid response")

    if results["status"] == "REQUEST_DENIED":
        raise Exception("API Key or other request denied error")

    if results["status"] == "OVER_QUERY_LIMIT":
        logging.warn("Hit Query Limit! Backing off for a bit.")
        time.sleep(5)  # sleep for 30 minutes
        lookup_placeid(place_id)

    if results["status"] == "ZERO_RESULTS":
        return None

    if not results["status"] == "OK":
        logging.error("Error results for %s", place_id)
        raise Exception("No results: {}".format(results["status"]))

    if not "result" in results:
        logging.error("No result for %s", place_id)
        raise Exception("No result: {}".format(place_id))

    return results["result"]


def place_autocomplete(
    query, region=None, api_key=None, return_full_response=False
):

    GOOGLE_PLACES_URL = (
        "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    )

    query_params = {}

    query_components = {}

    url_params = {
        "key": scrapy_settings.google_places_api_key,
        "input": query,
    }

    if region:
        query_params["region"] = region

    if "postal_code" in query:
        query_components["postal_code"] = query["postal_code"]

    if "country" in query:
        query_params["region"] = query["country"]
        query_components["country"] = query["country"]
        query.pop("country", None)

    url_params["components"] = "|".join(
        f"{k}:{v}" for k, v in query_components.items()
    )

    results = requests.get(GOOGLE_PLACES_URL, params=url_params).json()

    logging.debug(results)

    if not "status" in results:
        raise Exception("Invalid response")

    if results["status"] == "REQUEST_DENIED":
        raise Exception("API Key or other request denied error")

    if results["status"] == "OVER_QUERY_LIMIT":
        logging.warn("Hit Query Limit! Backing off for a bit.")
        time.sleep(5)  # sleep for 30 minutes
        return google_geocode(query, region, api_key, return_full_response)

    if results["status"] == "ZERO_RESULTS":
        return None

    if not results["status"] == "OK":
        logging.error("Error results for %s", query)
        raise Exception("No results: {}".format(results["status"]))

    if len(results["predictions"]) == 0:
        logging.error("No results for %s", query)
        return None

    cand = results["predictions"]
    return cand


def place_search(query, api_key=None, return_full_response=False):

    GOOGLE_PLACES_URL = (
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    )

    query_params = {}

    query_components = {}

    url_params = {
        "key": scrapy_settings.google_places_api_key,
        "input": query,
        "inputtype": "textquery",
        "language": "en-AU",
        # "fields": "basic"
        "fields": "name,geometry,place_id",
    }

    results = requests.get(GOOGLE_PLACES_URL, params=url_params).json()

    logging.debug(results)

    if not "status" in results:
        raise Exception("Invalid response")

    if results["status"] == "REQUEST_DENIED":
        raise Exception("API Key or other request denied error")

    if results["status"] == "OVER_QUERY_LIMIT":
        logging.warn("Hit Query Limit! Backing off for a bit.")
        time.sleep(5)  # sleep for 30 minutes
        return place_search(query)

    if results["status"] == "ZERO_RESULTS":
        return None

    if not results["status"] == "OK":
        logging.error("Error results for %s", query)
        raise Exception("No results: {}".format(results["status"]))

    if len(results["candidates"]) == 0:
        logging.error("No results for %s", query)
        return None

    cand = results["candidates"]
    return cand
