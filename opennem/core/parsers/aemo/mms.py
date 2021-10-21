"""
Parse AEMO MMS CSV format which can have multiple tables and definitions per CSV files.

"""

import csv
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError
from pydantic.fields import PrivateAttr

from opennem.pipelines.files import _fallback_download_handler
from opennem.schema.aemo.mms import MMSBase, get_mms_schema_for_table

_HAVE_PANDAS = False

try:
    import pandas as pd

    _HAVE_PANDAS = True
except ImportError:
    pass


logger = logging.getLogger(__name__)


# pylint: disable=no-self-argument
class AEMOTableSchema(BaseModel):
    name: str
    namespace: str
    fieldnames: List[str]
    _records: List[Union[Dict, BaseModel]] = []

    # optionally it has a schema
    _record_schema: Optional[BaseModel] = PrivateAttr()

    # the url this table was taken from if any
    url_source: Optional[str]

    # the original content ?!?!
    # @NOTE does this make sense .. (it doesnt because it can be super large)
    content_source: Optional[str]

    @property
    def full_name(self) -> str:
        return "{}_{}".format(self.namespace, self.name)

    @validator("name")
    def validate_name(cls, table_name: str) -> str:
        _table_name = table_name.strip().lower()

        return _table_name

    @validator("namespace")
    def validate_namespace(cls, namespace_name: str) -> str:
        _namespace_name = namespace_name.strip().lower()

        return _namespace_name

    @validator("fieldnames")
    def validate_fieldnames(cls, fieldnames: List[str]) -> List[str]:
        if not isinstance(fieldnames, list):
            return []

        _fieldnames = [i.lower() for i in fieldnames]

        return _fieldnames

    def set_schema(self, schema: BaseModel) -> bool:
        self._record_schema = schema

        return True

    @property
    def records(self) -> Any:
        _records = []

        for _r in self._records:
            if isinstance(_r, MMSBase):
                _records.append(_r.dict())
            if isinstance(_r, Dict):
                _records.append(_r)

        return _records

    def add_record(self, record: Union[Dict, BaseModel]) -> bool:
        if hasattr(self, "_record_schema") and self._record_schema:
            _record = None

            try:
                _record = self._record_schema(**record)  # type: ignore
            except ValidationError as e:
                val_errors = e.errors()

                for ve in val_errors:
                    ve_fieldname = ve["loc"][0]
                    ve_val = ""

                    if record and isinstance(record, dict) and ve_fieldname in record:
                        ve_val = record[ve_fieldname]

                    logger.error("{} has error: {} '{}'".format(ve_fieldname, ve["msg"], ve_val))
                return False

            self._records.append(_record)
        else:
            self._records.append(record)

        return True

    def to_frame(self) -> Any:
        """Return a pandas dataframe for the table"""
        if not _HAVE_PANDAS:
            return None

        _index_keys = []

        if hasattr(self, "_record_schema") and self._record_schema:
            if hasattr(self._record_schema, "_primary_keys"):
                _index_keys = self._record_schema._primary_keys  # type: ignore

        _df = pd.DataFrame(self.records)

        if len(_index_keys) > 0:
            logger.debug("Setting index to {}".format(_index_keys))
            _df = _df.set_index(_index_keys)

        return _df

    class Config:
        underscore_attrs_are_private = True


class AEMOTableSet(BaseModel):
    tables: List[AEMOTableSchema] = []

    @property
    def table_names(self) -> List[str]:
        _names: List[str] = []

        for _t in self.tables:
            _names.append(_t.full_name)

        return _names

    def has_table(self, table_name: str) -> bool:
        if not self.tables:
            return False

        if len(self.tables) < 1:
            return False

        table_lookup = list(filter(lambda t: t.full_name == table_name, self.tables))

        return len(table_lookup) > 0

    def add_table(self, table: AEMOTableSchema) -> bool:
        self.tables.append(table)

        return True

    def get_table(self, table_name: str) -> Optional[AEMOTableSchema]:
        table_name = table_name.upper()

        if not self.has_table(table_name):
            return None
            # raise Exception("Table not found: {}".format(table_name))

        table_lookup = list(filter(lambda t: t.full_name == table_name, self.tables))

        return table_lookup.pop()


class AEMOParserException(Exception):
    pass


AEMO_ROW_HEADER_TYPES = ["C", "I", "D"]


def parse_aemo_mms_csv(
    content: str,
    table_set: Optional[AEMOTableSet] = None,
    namespace_filter: Optional[List[str]] = None,
) -> AEMOTableSet:
    """
    Parse AEMO CSV's into schemas and return a table set

    Exception raised on error and logs malformed CSVs
    """

    if not table_set:
        table_set = AEMOTableSet()

    content_split = content.splitlines()

    # @NOTE more efficient csv parsing
    datacsv = csv.reader(content_split)

    # init all the parser vars
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
            table_fields = [i.lower() for i in row[4:]]

            table_full_name = "{}_{}".format(table_namespace.lower(), table_name.lower())

            if namespace_filter and table_namespace.lower() not in namespace_filter:
                table_current = None
                continue

            if table_set.has_table(table_full_name):
                table_current = table_set.get_table(table_full_name)
            else:
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
                continue

            values = row[4:]

            if len(values) != len(table_current.fieldnames):
                logger.error("Malformed AEMO csv - length mismatch between records and fields")
                continue

            record = dict(zip(table_current.fieldnames, values))

            table_current.add_record(record)

    return table_set


def parse_aemo_urls(urls: List[str]) -> AEMOTableSet:
    """Parse a list of URLs into an AEMOTableSet"""
    aemo = AEMOTableSet()

    for url in urls:
        csv_content = _fallback_download_handler(url)

        if not csv_content:
            logger.error("Could not parse URL: {}".format(url))
            continue

        csv_content_decoded = csv_content.decode("utf-8")
        aemo = parse_aemo_mms_csv(csv_content_decoded, aemo)

    return aemo


def parse_aemo_directory(directory_path: str) -> AEMOTableSet:
    pass
