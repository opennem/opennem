from itertools import groupby

from opennem.core.normalizers import station_name_cleaner
from opennem.utils.pipelines import check_spider_pipeline


class RegistrationExemptionGrouperPipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not "generators" in item:
            raise Exception("No generators found in item pipeline failed")

        generators = item["generators"]

        # Add clean station names
        generators = [
            {**i, "name": station_name_cleaner(i["station_name"])}
            for i in generators
        ]

        # sort by name
        generators = sorted(generators, key=lambda k: k["name"])

        generators_grouped = {}

        for k, v in groupby(generators, key=lambda v: v["name"]):
            if not k in generators_grouped:
                generators_grouped[k] = []

            generators_grouped[k] += list(v)

        return {**item, "generators": generators_grouped}
