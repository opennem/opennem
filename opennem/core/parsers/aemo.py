"""
    Parse AEMO CSV format which can have multiple
    tables and definitions per CSV files.

"""

import csv
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError
from pydantic.fields import PrivateAttr

from opennem.schema.aemo.mms import get_mms_schema_for_table

logger = logging.getLogger(__name__)


# pylint: disable=no-self-argument
class AEMOTableSchema(BaseModel):
    name: str
    namespace: str
    fieldnames: List[str]
    records: List[Union[Dict, BaseModel]] = []

    # optionally it has a schema
    _record_schema: Optional[BaseModel] = PrivateAttr()

    # the url this table was taken from if any
    url_source: Optional[str]

    # the original content ?!?!
    # @NOTE does this make sense ..
    content_source: Optional[str]

    @property
    def full_name(self) -> str:
        return "{}_{}".format(self.namespace, self.name)

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

    def set_schema(self, schema: BaseModel) -> bool:
        self._record_schema = schema

        return True

    def get_records(self) -> Any:
        return self.records

    def add_record(self, record: Union[Dict, BaseModel]) -> bool:
        if self._record_schema:
            _record = None

            try:
                _record = self._record_schema(**record)  # type: ignore
            except ValidationError as e:
                val_errors = e.errors()

                for ve in val_errors:
                    ve_fieldname = ve["loc"][0]
                    ve_val = ""

                    if (
                        record
                        and isinstance(record, dict)
                        and ve_fieldname in record
                    ):
                        ve_val = record[ve_fieldname]

                    logger.error(
                        "{} has error: {} '{}'".format(
                            ve_fieldname, ve["msg"], ve_val
                        )
                    )
                return False

            self.records.append(_record)
        else:
            self.records.append(record)

        return True

    class Config:
        underscore_attrs_are_private = True


class AEMOTableSet(BaseModel):
    tables: List[AEMOTableSchema] = []

    def has_table(self, table_name: str) -> bool:
        if not self.tables:
            return False

        if len(self.tables) < 1:
            return False

        table_name = table_name.upper()

        table_lookup = list(
            filter(lambda t: t.full_name == table_name, self.tables)
        )

        return len(table_lookup) > 0

    def add_table(self, table: AEMOTableSchema) -> bool:
        self.tables.append(table)

        return True

    def get_table(self, table_name: str) -> AEMOTableSchema:
        table_name = table_name.upper()

        if not self.has_table(table_name):
            raise Exception("Table not found: {}".format(table_name))

        table_lookup = list(
            filter(lambda t: t.full_name == table_name, self.tables)
        )

        return table_lookup.pop()


class AEMOParserException(Exception):
    pass


AEMO_ROW_HEADER_TYPES = ["C", "I", "D"]


def parse_aemo_csv(content: str) -> AEMOTableSet:
    """
    Parse AEMO CSV's into schemas and return a table set

    Exception raised on error and logs malformed CSVs
    """
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

            table_namespace = row[1]
            table_name = row[2]
            table_fields = row[4:]

            table_current = AEMOTableSchema(
                name=table_name,
                namespace=table_namespace,
                fields=table_fields,
                fieldnames=table_fields,
            )

            # do we have a custom shema for the table?
            table_schema = get_mms_schema_for_table(table_current.full_name)

            if table_schema:
                table_current.set_schema(table_schema)

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
