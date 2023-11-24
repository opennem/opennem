#!/usr/bin/env python3
import logging

from opennem.api.stats.schema import load_opennem_dataset_from_url

logger = logging.getLogger("opennem.test.compare_dev_prod")


POWER_URL = "https://data.{dev}opennem.org.au/v3/stats/au/NEM/power/7d.json"


def get_url(is_dev: bool = False) -> str:
    return POWER_URL.format(dev="dev." if is_dev else "")


def run_test() -> None:
    prod_url = get_url(is_dev=False)
    dev_url = get_url(is_dev=True)

    logger.info(f"{prod_url=} {dev_url=}")

    prod_data = load_opennem_dataset_from_url(prod_url)
    dev_data = load_opennem_dataset_from_url(dev_url)

    prod_ids = [series.id for series in prod_data.data if series.id]
    dev_ids = [series.id for series in dev_data.data if series.id]

    # check ids
    assert len(prod_ids) == len(dev_ids), "Have the same number of ids"
    assert set(prod_ids) == set(dev_ids), "Have the same ids"

    for id in dev_ids:
        dev_series = dev_data.get_id(id)
        prod_series = prod_data.get_id(id)

        if not prod_series:
            logger.error(f"Missing prod series {id=}")
            continue

        assert dev_series.code == prod_series.code, "has code"

        if prod_series.fuel_tech:
            assert dev_series.fuel_tech == prod_series.fuel_tech, "has code"


if __name__ == "__main__":
    run_test()
