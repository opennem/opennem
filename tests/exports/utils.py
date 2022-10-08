""" Export Test Utilities """

from dataclasses import dataclass
from enum import Enum

from opennem.api.stats.schema import OpennemDataHistory, OpennemDataSet, load_opennem_dataset_from_file
from opennem.utils.tests import TEST_FIXTURE_PATH

ValidNumber = float | int

REGIONS = ["NSW1", "VIC1", "SA1", "QLD1", "TAS1"]


class SeriesType(str, Enum):
    power = "power"
    emissions = "emissions"
    energy = "energy"
    demand = "demand"
    price = "price"
    temperature = "temperature"


@dataclass
class RegionSeries:
    power: OpennemDataSet
    daily: OpennemDataSet
    weekly: OpennemDataSet
    all: OpennemDataSet


FIXTURE_SET: dict[str, RegionSeries] = {}


def load_region_fixtures() -> None:
    for region in REGIONS:
        if region not in FIXTURE_SET:
            FIXTURE_SET[region] = RegionSeries(
                power=load_opennem_dataset_from_file(TEST_FIXTURE_PATH / f"nem_{region.lower()}_7d.json"),
                daily=load_opennem_dataset_from_file(TEST_FIXTURE_PATH / f"nem_{region.lower()}_1y.json"),
                weekly=load_opennem_dataset_from_file(TEST_FIXTURE_PATH / f"nem_{region.lower()}_week.json"),
                all=load_opennem_dataset_from_file(TEST_FIXTURE_PATH / f"nem_{region.lower()}_all.json"),
            )


load_region_fixtures()
