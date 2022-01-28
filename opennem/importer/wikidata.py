import csv
import json
import logging
from urllib.parse import urlparse

import requests
import wikipedia
from PIL import Image

from opennem.api.photo.controllers import write_photo_to_s3
from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.db import SessionLocal
from opennem.db.models.opennem import Photo, Station
from opennem.utils.images import image_get_crypto_hash, img_to_buffer

logger = logging.getLogger("opennem.importer.wikidata")
logging.getLogger("PIL").setLevel(logging.ERROR)


def article_from_wikipedia(url: str) -> str:
    """
    Return the article name from a wikipedia url
    """
    path = urlparse(url).path

    if not path:
        return ""

    return path.split("/")[2]


def dataid_from_url(url: str) -> str:
    """
    Return the Q id from a wikidata url
    """
    path = urlparse(url).path

    if not path:
        return ""

    return path.split("/")[2]


def wikidata_join() -> None:
    """Attempts to join the wikidata to OpenNEM stations based
    on the name"""

    session = SessionLocal()

    wikidata = load_data("wikidata-parsed.json", from_project=True)

    # Use a better query
    # engine = get_database_engine()

    # station_lookup_query = """

    # """

    for entry in wikidata:
        station_name = entry.get("name")

        station_lookup = session.query(Station).filter(Station.name == station_name).all()

        if len(station_lookup) == 0:
            logger.info("Didn't find a station for {}".format(station_name))

        if len(station_lookup) == 1:
            station = station_lookup.pop()

            station.description = entry.get("description")
            station.wikipedia_link = entry.get("wikipedia")
            station.wikidata_id = entry.get("wikidata_id")

            session.add(station)
            logger.info("Updated station {}".format(station_name))

        if len(station_lookup) > 1:
            logger.info("Found multiple for station {}".format(station_name))

    session.commit()


def wikidata_join_mapping() -> None:
    """Attempts to join the wikidata to OpenNEM stations using the
    csv file with mappings"""

    session = SessionLocal()

    wikidata = load_data("wikidata-parsed.json", from_project=True)

    wikidata_mappings = None

    with open("opennem/data/wikidata_mappings.csv") as fh:
        csvreader = csv.DictReader(
            fh,
            fieldnames=[
                "code",
                "name",
                "network_id",
                "network_region",
                "fueltech_id",
                "wikidata_id",
            ],
        )
        wikidata_mappings = {
            i["code"]: i["wikidata_id"]
            for i in list(csvreader)
            if i["wikidata_id"] and i["code"] != "code"
        }

    for station_code, wikidata_id in wikidata_mappings.items():
        wikidata_record_lookup = list(filter(lambda x: x["wikidata_id"] == wikidata_id, wikidata))

        if len(wikidata_record_lookup) == 0:
            logger.error("Could not find {}".format(wikidata_id))
            continue

        wikidata_record = wikidata_record_lookup.pop()

        station = session.query(Station).filter(Station.code == station_code).one_or_none()

        if not station:
            logger.error("Didn't find a station for {}".format(station_code))
            continue

        station.description = wikidata_record.get("description")
        station.wikipedia_link = wikidata_record.get("wikipedia")
        station.wikidata_id = wikidata_record.get("wikidata_id")

        session.add(station)
        logger.info("Updated station {}".format(station_code))

    session.commit()


def wikidata_parse() -> None:

    # query: https://w.wiki/dVi
    # download the simplified json and save to wikidata.json
    wikidata = load_data("wikidata.json", from_project=True)

    out_entries = []
    total_entries = len(wikidata)
    current = 0

    for entry in wikidata:
        wikilink = article_from_wikipedia(entry["article"])
        wikidata = dataid_from_url(entry["item"])
        station_name = station_name_cleaner(entry["itemLabel"])

        description = None

        try:
            description = wikipedia.summary(wikilink)
        except Exception as e:
            print(e)

        new_entry = {
            "wikipedia": entry["article"],
            "wikidata": entry["item"],
            "wiki_id": wikilink,
            "wikidata_id": wikidata,
            "name": station_name,
            "name_original": entry["itemLabel"],
            "description": description,
        }

        out_entries.append(new_entry)
        current += 1

        print("Done {} of {}".format(current, total_entries))

    with open("data/wikidata-parsed.json", "w") as fh:
        json.dump(out_entries, fh)


def get_image(image_url: str) -> Image:
    img = None

    try:
        img = Image.open(requests.get(image_url, stream=True).raw)
    except Exception:
        logger.error("Error parsing: %s", image_url)
        return None

    return img


def wikidata_photos() -> None:
    """Attach wikidata photos to stations"""
    session = SessionLocal()
    wikidata = load_data("wikidata-photos.json", from_project=True)

    for entry in wikidata:
        image_url = entry["thumb"]
        name = entry["itemLabel"]
        wiki_id = dataid_from_url(entry["item"])

        stations = session.query(Station).filter(Station.wikidata_id == wiki_id).all()

        if not stations or len(stations) == 0:
            logger.error("Could not find station {}".format(name))
            continue

        for station in stations:

            img = get_image(image_url)

            if not img:
                logger.error("No image for {}".format(name))
                continue

            hash_id = image_get_crypto_hash(img)[-8:]
            file_name = "{}_{}_{}.{}".format(hash_id, name.replace(" ", "_"), "original", "jpeg")

            photo = Photo(
                name=file_name,
                hash_id=hash_id,
                width=img.size[0],
                height=img.size[1],
                original_url=image_url,
            )

            img_buff = img_to_buffer(img)

            write_photo_to_s3(file_name, img_buff)

            if station:
                station.photos.append(photo)

            # Thumbnail copy (and code copy!)

            img.thumbnail((280, 340))
            hash_id = image_get_crypto_hash(img)[-8:]

            file_name = "{}_{}_{}.{}".format(hash_id, name.replace(" ", "_"), img.size[0], "jpeg")

            photo_thumb = Photo(
                name=file_name,
                hash_id=hash_id,
                width=img.size[0],
                height=img.size[1],
                original_url=image_url,
            )

            img_buff = img_to_buffer(img)
            write_photo_to_s3(file_name, img_buff)

            if station:
                station.photos.append(photo_thumb)

            session.add(photo)
            session.add(photo_thumb)

            if station:
                session.add(station)

            session.commit()


if __name__ == "__main__":
    wikidata_photos()
