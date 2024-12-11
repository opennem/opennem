""" "
Takes an OpenNEM JSON output and debugs it

"""

import logging

from opennem.utils.datatable import datatable_print
from opennem.utils.http import http

logger = logging.getLogger("opennem.inspector")


def inspect_opennem_json(url: str):
    logger.info(f"Getting {url}")
    response = http.get(url)

    if not response.ok:
        logger.error(f"Failed to get {url}")
        return

    data = response.json()

    if "data" not in data:
        logger.error(f"No data in {url}")
        return

    opennem_data = data["data"]
    data_items = []

    for item in opennem_data:
        if "history" not in item:
            logger.error(f"No history in {item.get('id')}")
            continue

        data_items.append(
            {
                "id": item["id"],
                "interval": item["history"]["interval"],
                "unit": item["units"],
                "date_start": item["history"]["start"],
                "date_end": item["history"]["last"],
                "items": len(item["history"]["data"]),
                "first_item": item["history"]["data"][0],
                "last_item": item["history"]["data"][-1],
            }
        )

    print(f"Version: {data['version']}")
    print(f"Updated: {data['created_at']}")
    datatable_print(data_items)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://data.dev.opennem.org.au/v4/stats/au/NEM/NSW1/energy/2024.json"

    inspect_opennem_json(test_url)
