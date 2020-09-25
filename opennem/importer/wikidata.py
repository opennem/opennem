from pprint import pprint
from urllib.parse import urlparse

import wikipedia

from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.db import SessionLocal
from opennem.db.models.opennem import Station


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


import json
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


if __name__ == "__main__":
    wikidata_join()
