import json
import logging
from pprint import pprint
from urllib.parse import urlparse

import requests
import wikipedia
from PIL import Image

from opennem.api.photo.controllers import img_to_buffer, write_photo_to_s3
from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.db import SessionLocal
from opennem.db.models.opennem import Photo, Station

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def wikidata_join():
    session = SessionLocal()

    wikidata = load_data("wikidata-parsed.json", from_project=True)

    # session.add()

    for entry in wikidata:
        station_name = entry.get("name")

        station_lookup = (
            session.query(Station).filter(Station.name == station_name).all()
        )

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


def wikidata_parse():

    # query: https://w.wiki/dVi
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


def get_image(image_url):
    img = None

    try:
        img = Image.open(requests.get(image_url, stream=True).raw)
    except Exception:
        logger.error("Error parsing: %s", image_url)
        return None

    return img


def wikidata_photos():
    session = SessionLocal()
    wikidata = load_data("wikidata-photos.json", from_project=True)

    for entry in wikidata:
        image_url = entry["thumb"]
        name = entry["itemLabel"]
        wiki_id = dataid_from_url(entry["item"])

        station = (
            session.query(Station)
            .filter(Station.wikidata_id == wiki_id)
            .one_or_none()
        )

        if not station:
            print("Could not find station {}".format(name))
            # continue

        img = get_image(image_url)

        if not img:
            print("No image for {}".format(name))
            continue

        # file_name = urlparse(image_url).path.split("/")[-1:]
        file_name = "{}_{}.{}".format(
            name.replace(" ", "_"), "original", "jpeg"
        )

        photo = Photo(
            name=file_name,
            width=img.size[0],
            height=img.size[1],
            original_url=image_url,
        )

        img_buff = img_to_buffer(img)

        write_photo_to_s3(file_name, img_buff)

        if station:
            station.photos.append(photo)

        img.thumbnail((280, 340))

        file_name = "{}_{}.{}".format(
            name.replace(" ", "_"), img.size[0], "jpeg"
        )

        photo_thumb = Photo(
            name=file_name,
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
    wikidata_join()
    wikidata_photos()
