from itertools import groupby


class RegistrationExemptionGrouperPipeline(object):
    def parse_item(self, item, spider):
        if not "generators" in item:
            raise Exception("No generators found in item pipeline failed")

        generators = item["generators"]

        generators_grouped = {}

        for k, v in groupby(generators, key=lambda v: v["station_name"]):
            if not k in generators_grouped:
                generators_grouped[k] = []

            generators_grouped[k] += list(v)

        return {**item, "generators": generators_grouped}
