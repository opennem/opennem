"""
    Parse AEMO CSV format which can have multiple
    tables and definitions per CSV files.

"""

import csv
import logging
from typing import Dict, List, Optional

from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


# pylint: disable=no-self-argument
class AEMOTableSchema(BaseModel):
    name: str
    namespace: Optional[str]
    fieldnames: List[str]
    records: List[Dict] = []

    # the url this table was taken from if any
    url_source: Optional[str]

    # the original content ?!?!
    # @NOTE does this make sense ..
    content_source: Optional[str]

    @property
    def full_name(self) -> str:
        return "{}_{}".format(self.name, self.namespace)

    @validator("name")
    def validate_name(cls, table_name: str) -> str:
        _table_name = table_name.strip().upper()

        return _table_name

    @validator("namespace")
    def validate_namespace(cls, namespace_name: str) -> str:
        _namespace_name = namespace_name.strip().upper()

        return _namespace_name

    @validator("fieldnames")
    def validate_fieldnames(cls, fieldnames: List[str]) -> List[str]:
        if not isinstance(fieldnames, list):
            return []

        _fieldnames = [i.strip() for i in fieldnames]

        return _fieldnames

    def add_record(self, record: Dict) -> bool:
        # @TODO validate + table schemas! should be coool
        self.records.append(record)

        return True


class AEMOTableSet(BaseModel):
    tables: List[AEMOTableSchema] = []

    def has_table(self, table_name: str) -> bool:
        if not self.tables:
            return False

        if len(self.tables) < 1:
            return False

        table_lookup = list(
            filter(lambda t: t.name == table_name, self.tables)
        )

        return len(table_lookup) > 0

    def add_table(self, table: AEMOTableSchema) -> bool:
        self.tables.append(table)

        return True


class AEMOParserException(Exception):
    pass


AEMO_ROW_HEADER_TYPES = ["C", "I", "D"]


def parse_aemo_csv(content: str) -> AEMOTableSet:
    content_split = content.splitlines()

    datacsv = csv.reader(content_split)

    # init all the parser vars
    table_set = AEMOTableSet()
    table_current = None

    for row in datacsv:
        if not row or type(row) is not list or len(row) < 1:
            continue

        record_type = row[0].strip().upper()

        if record_type not in AEMO_ROW_HEADER_TYPES:
            logger.info("Skipping row, invalid type: {}".format(record_type))
            continue

        # new table set
        if record_type == "C":
            # @TODO csv meta stored in table
            if table_current:
                table_set.add_table(table_current)

        # new table
        elif record_type == "I":
            if table_current:
                table_set.add_table(table_current)

            table_name = row[1]
            table_namespace = row[2]
            table_fields = row[4:]

            table_current = AEMOTableSchema(
                name=table_name,
                namespace=table_namespace,
                fields=table_fields,
                fieldnames=table_fields,
            )

        # new record
        elif record_type == "D":
            if not table_current:
                logger.error(
                    "Malformed AEMO csv - field records before table definition"
                )
                continue

            values = row[4:]

            if len(values) != len(table_current.fieldnames):
                logger.error(
                    "Malformed AEMO csv - length mismatch between records and fields"
                )
                continue

            record = dict(zip(table_current.fieldnames, values))

            table_current.add_record(record)

    return table_set
