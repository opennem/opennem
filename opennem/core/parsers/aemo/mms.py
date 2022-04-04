"""
Parse AEMO MMS CSV format which can have multiple tables and definitions per CSV files.

"""

import csv
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError
from pydantic.fields import PrivateAttr

from opennem.core.downloader import url_downloader
from opennem.core.normalizers import normalize_duid
from opennem.schema.aemo.mms import MMSBaseClass, get_mms_schema_for_table
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import parse_date
from opennem.utils.version import get_version

_HAVE_PANDAS = False

try:
    import pandas as pd

    _HAVE_PANDAS = True
except ImportError:
    pass


logger = logging.getLogger(__name__)


# pylint: disable=no-self-argument
class AEMOTableSchema(BaseConfig):
    name: str
    namespace: str
    fieldnames: List[str]
    _records: List[Union[MMSBaseClass, Dict[str, Any]]] = []

    # optionally it has a schema
    _record_schema: Optional[MMSBaseClass] = PrivateAttr()

    # the url this table was taken from if any
    url_source: Optional[str]

    # the original content ?!?!
    # @NOTE does this make sense .. (it doesnt because it can be super large)
    content_source: Optional[str]

    @property
    def full_name(self) -> str:
        return "{}_{}".format(self.namespace, self.name)

    @property
    def primary_key(self) -> Optional[List[str]]:
        if (
            hasattr(self, "_record_schema")
            and isinstance(self._record_schema, MMSBaseClass)
            and hasattr(self._record_schema, "_primary_keys")
        ):
            return self._record_schema._primary_keys

        return None

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

    def set_schema(self, schema: MMSBaseClass) -> bool:
        self._record_schema = schema

        return True

    @property
    def records(self) -> List[Union[MMSBaseClass, Dict[str, Any]]]:
        return self._records

    def add_record(self, record: Union[Dict, MMSBaseClass]) -> bool:
        if isinstance(record, dict) and hasattr(self, "_record_schema") and self._record_schema:
            _record = None

            if not isinstance(record, dict):
                raise Exception("Could not add record, not a dict: {}".format(record))

            try:
                _record = self._record_schema(**record)  # type: ignore
            except ValidationError as e:
                val_errors = e.errors()
                logger.debug(record)

                for ve in val_errors:
                    ve_fieldname = ve["loc"][0]
                    ve_val = ""

                    if record and isinstance(record, dict) and ve_fieldname in record:
                        ve_val = record[ve_fieldname]

                return False
            except Exception as e:
                logger.error("Record error: {}".format(e))
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

        _df = pd.DataFrame(self.records)

        if hasattr(self, "_record_schema") and self._record_schema:
            if hasattr(self._record_schema, "_primary_keys"):
                _index_keys = self._record_schema._primary_keys  # type: ignore

        if len(_index_keys) > 0:
            logger.debug("Setting index to {}".format(_index_keys))
            try:
                _df = _df.set_index(_index_keys)
            except KeyError:
                logger.warn("Could not set index with columns: {}".format(", ".join(_index_keys)))

        return _df

    class Config:
        underscore_attrs_are_private = True


class AEMOTableSet(BaseModel):
    version: str = get_version()
    generated: datetime = datetime.now()
    tables: List[AEMOTableSchema] = []

    @property
    def table_names(self) -> List[str]:
        _names: List[str] = []

        for _t in self.tables:
            _names.append(_t.full_name)

        return _names

    def has_table(self, table_name: str) -> bool:
        found_table: bool = False

        if not self.tables:
            return False

        if len(self.tables) < 1:
            return False

        table_lookup = list(filter(lambda t: t.full_name == table_name, self.tables))

        if len(table_lookup) > 0:
            return True

        # if not found search by name only
        # @NOTE this might lead to bugs
        table_lookup = list(filter(lambda t: t.name == table_name, self.tables))

        if len(table_lookup) > 0:
            return True

        return found_table

    def add_table(self, table: AEMOTableSchema) -> bool:
        _existing_table = self.get_table(table.full_name)

        if _existing_table:
            for r in table.records:
                _existing_table.add_record(r)
        else:
            self.tables.append(table)

        return True

    def get_table(self, table_name: str) -> Optional[AEMOTableSchema]:
        if not self.has_table(table_name):
            return None

        table_lookup = list(filter(lambda t: t.full_name == table_name, self.tables))

        if table_lookup:
            return table_lookup.pop()

        table_lookup = list(filter(lambda t: t.name == table_name, self.tables))

        if table_lookup:
            return table_lookup.pop()

        logger.debug(
            "Looking up table: {} amongst ({})".format(
                table_name, ", ".join([i.name for i in self.tables])
            )
        )

        return None


class AEMOParserException(Exception):
    pass


AEMO_ROW_HEADER_TYPES = ["C", "I", "D"]

MMS_DATE_FIELDS = ["settlementdate", "tradinginterval", "lastchanged", "interval_datetime"]

MMS_DUID_FIELDS = ["duid"]


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
        # @TODO switch to match
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

            if namespace_filter and table_namespace.lower() not in namespace_filter:
                table_current = None
                continue

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
                logger.error("Have a record but not currently in a table")
                continue

            values = row[4:]

            if len(values) != len(table_current.fieldnames):
                logger.error("Malformed AEMO csv - length mismatch between records and fields")
                continue

            record = dict(zip(table_current.fieldnames, values))

            for field, fieldvalue in record.items():
                if field in MMS_DATE_FIELDS:
                    fieldvalue_parsed = parse_date(fieldvalue, network=NetworkNEM)
                    record[field] = fieldvalue_parsed

                if field in MMS_DUID_FIELDS:
                    fieldvalue_parsed = normalize_duid(fieldvalue)
                    record[field] = fieldvalue_parsed

            table_current.add_record(record)

        else:
            logger.error(f"Invalid AEMO record type: {record_type}")

    return table_set


def parse_aemo_urls(urls: List[str]) -> AEMOTableSet:
    """Parse a list of URLs into an AEMOTableSet"""
    aemo = AEMOTableSet()

    for url in urls:
        csv_content = url_downloader(url)

        if not csv_content:
            logger.error("Could not parse URL: {}".format(url))
            continue

        csv_content_decoded = csv_content.decode("utf-8")
        aemo = parse_aemo_mms_csv(csv_content_decoded, aemo)

    return aemo


def parse_aemo_directory(directory_path: str) -> AEMOTableSet:
    pass


# debug entry point
if __name__ == "__main__":
    url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202204081455_0000000360913773.zip"

    r = parse_aemo_urls([url])
    assert r.has_table("unit_scada"), "has table"

    print("has table and done")
