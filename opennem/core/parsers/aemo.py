import csv
from typing import Dict, List, Optional

from pydantic.main import BaseModel


class AEMOTableSchema(BaseModel):
    name: str
    namespace: Optional[str]
    fieldnames: List[str]
    records: List[Dict]


class AEMOTableSet(BaseModel):
    tables: List[AEMOTableSchema]


def parse_aemo_csv(content: str) -> AEMOTableSet:
    content_split = content.splitlines()

    datacsv = csv.reader(content_split)

    for row in datacsv:
        if not row or type(row) is not list or len(row) < 1:
            continue

        record_type = row[0]

        if record_type == "C":
            # @TODO csv meta stored in table
            if table["name"] is not None:
                table_name = table["name"]

                if table_name in item["tables"]:
                    item["tables"][table_name]["records"] += table["records"]
                else:
                    item["tables"][table_name] = table

        elif record_type == "I":
            if table["name"] is not None:
                table_name = table["name"]

                if table_name in item["tables"]:
                    item["tables"][table_name]["records"] += table["records"]
                else:
                    item["tables"][table_name] = table

            table = {}
            table["name"] = "{}_{}".format(row[1], row[2])
            table["fields"] = fields = row[4:]
            table["records"] = []

        elif record_type == "D":
            values = row[4:]
            record = dict(zip(table["fields"], values))

            table["records"].append(record)


