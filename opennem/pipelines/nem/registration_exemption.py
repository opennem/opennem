from itertools import groupby

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.normalizers import station_name_cleaner
from opennem.utils.pipelines import check_spider_pipeline


class RegistrationExemptionGrouperPipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not "generators" in item:
            raise Exception("No generators found in item pipeline failed")

        generators = item["generators"]

        # Add clean station names and if group_by name
        generators = [
            {
                **i,
                "name": station_name_cleaner(i["station_name"]),
                "name_join": False
                if facility_station_join_by_name(
                    station_name_cleaner(i["station_name"])
                )
                else i["duid"],
            }
            for i in generators
        ]

        # sort by name

        generators_grouped = {}

        for k, v in groupby(
            generators, key=lambda v: (v["name"], v["name_join"])
        ):
            key = k[0]
            if not key in generators_grouped:
                generators_grouped[key] = []

            generators_grouped[key] += list(v)

        return {**item, "generators": generators_grouped}
