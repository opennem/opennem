import logging
from datetime import datetime
from itertools import groupby
from typing import Optional

from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class AEMOMMSDudetailSummaryGrouper(object):
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """

            `25/10/1998  12:00:00 am` => d

        """
        date_string_components = date_string.strip().split(" ")

        if len(date_string_components) < 2:
            raise Exception("Error parsing date: {}".format(date_string))

        date_part = date_string_components[0]

        dt = None

        try:
            dt = datetime.strptime(date_part, "%Y/%m/%d")
        except ValueError:
            raise Exception("Error parsing date: {}".format(date_string))

        # AEMO sets dates to this value when they mean None
        # if dt.year == 2999:
        # return None

        return dt

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        if not "tables" in item:
            logger.error(item)
            raise Exception("No tables passed to pipeline")

        tables = item["tables"]
        table = tables.pop()

        records = table["records"]

        records = [
            {
                "date_start": self.parse_date(i["START_DATE"]),
                "date_end": self.parse_date(i["END_DATE"]),
                "DUID": i["DUID"],
                "REGIONID": i["REGIONID"],
                "STATIONID": i["STATIONID"],
                "PARTICIPANTID": i["PARTICIPANTID"],
                "DISPATCHTYPE": i["DISPATCHTYPE"]
                # "DUID": i["DUID"],
                # **i,
            }
            for i in records
            # if i["DISPATCHTYPE"] == "GENERATOR"
        ]

        grouped_records = {}

        # First pass sorts facilities into stations
        for k, v in groupby(records, lambda x: (x["STATIONID"], x["DUID"])):
            key = k[0]
            duid = k[1]
            if not key in grouped_records:
                grouped_records[key] = {}
                grouped_records[key]["id"] = k[0]
                # grouped_records[key]["participant"] = v[0]["PARTICIPANTID"]
                grouped_records[key]["details"] = {}
                grouped_records[key]["facilities"] = []

            if not duid in grouped_records[key]["details"]:
                grouped_records[key]["details"][duid] = []

            grouped_records[key]["details"][duid] += list(v)

        # Second pass flatten the records and we should get start and end dates and a derived status
        for rec in grouped_records.keys():
            for facility_group, facility_group_records in grouped_records[rec][
                "details"
            ].items():

                date_end_min = min(
                    facility_group_records, key=lambda x: x["date_end"]
                )
                date_end_max = max(
                    facility_group_records, key=lambda x: x["date_end"]
                )
                date_start_min = min(
                    facility_group_records, key=lambda x: x["date_start"]
                )

                # print(date_end_min, date_start_min, date_end_max)

                grouped_rec = {
                    **date_end_max,
                    "date_start": date_start_min["date_start"],
                }

                if grouped_rec["date_end"].year == 2999:
                    grouped_rec["date_end"] = None

                grouped_records[rec]["facilities"].append(grouped_rec)

        grouped_records = [
            {"id": i, "facilities": v["facilities"]}
            for i, v in grouped_records.items()
        ]

        return grouped_records
