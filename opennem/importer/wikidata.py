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


def run():
    session = SessionLocal()
    wikidata = load_data("wikidata.json", from_project=True)

    for entry in wikidata:
        wikilink = article_from_wikipedia(entry["article"])
        wikidata = dataid_from_url(entry["item"])
        station_name = station_name_cleaner(entry["itemLabel"])

        station = (
            session.query(Station).filter(Station.name == station_name).first()
        )

        if station:
            # print("found")
            print(wikilink, wikidata, station_name)

            description = wikipedia.summary(wikilink)
            station.description = description
            station.wikipedia_link = wikilink
            station.wikidata_id = wikidata

            session.add(station)

    session.commit()


if __name__ == "__main__":
    run()
