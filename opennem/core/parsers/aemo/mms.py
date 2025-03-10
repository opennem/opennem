"""
Parse AEMO MMS CSV format which can have multiple tables and definitions per CSV files.

"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opennem.core.downloader import url_downloader
from opennem.core.normalizers import normalize_duid
from opennem.schema.core import BaseConfig
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)


# pylint: disable=no-self-argument
class AEMOTableSchema(BaseConfig):
    name: str
    namespace: str
    fieldnames: list[str]
    records: list[dict[str, Any]] = Field(default_factory=list)

    # the url this table was taken from if any
    url_source: str | None = None

    # the original content ?!?!
    # @NOTE does this make sense .. (it doesnt because it can be super large)
    content_source: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.namespace}_{self.name}"

    @field_validator("name")
    @classmethod
    def validate_name(cls, table_name: str) -> str:
        _table_name = table_name.strip().lower()

        return _table_name

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, namespace_name: str) -> str:
        _namespace_name = namespace_name.strip().lower()

        return _namespace_name

    @field_validator("fieldnames")
    @classmethod
    def validate_fieldnames(cls, fieldnames: list[str]) -> list[str]:
        if not isinstance(fieldnames, list):
            return []

        _fieldnames = [i.lower() for i in fieldnames]

        return _fieldnames

    def add_record(self, record: dict, values_only: bool = False) -> bool:
        if values_only and isinstance(record, dict):
            self.records.append(list(record.values()))
        elif values_only and isinstance(record, list):
            self.records.append(record)
        else:
            self.records.append(record)

        return True

    def to_csv(self, filename: str) -> None:
        logger.info(f"Writing table {self.full_name} with {len(self.records)} records")

        with open(filename, "w") as fh:
            csvwriter = csv.DictWriter(fh, fieldnames=self.fieldnames)
            csvwriter.writeheader()

            for record in self.records:
                csvwriter.writerow(dict(zip(self.fieldnames, record, strict=True)))

        logger.info(f"Wrote records to {self.full_name}")

    model_config = ConfigDict()


class AEMOTableSet(BaseModel):
    version: str = get_version()
    generated: datetime = datetime.now()
    tables: list[AEMOTableSchema] = []

    @property
    def table_names(self) -> list[str]:
        _names: list[str] = []

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

    def add_table(self, table: AEMOTableSchema, values_only: bool = False) -> bool:
        _existing_table = self.get_table(table.full_name)

        if _existing_table:
            for r in table.records:
                _existing_table.add_record(r, values_only=values_only)
        else:
            self.tables.append(table)

        return True

    def get_table(self, table_name: str) -> AEMOTableSchema | None:
        if not self.has_table(table_name):
            return None

        table_lookup = list(filter(lambda t: t.full_name == table_name, self.tables))

        if table_lookup:
            return table_lookup.pop()

        table_lookup = list(filter(lambda t: t.name == table_name, self.tables))

        if table_lookup:
            return table_lookup.pop()

        logger.debug("Looking up table: {} amongst ({})".format(table_name, ", ".join([i.name for i in self.tables])))

        return None


class AEMOParserException(Exception):
    pass


AEMO_ROW_HEADER_TYPES = ["C", "I", "D"]

MMS_DUID_FIELDS = ["duid"]


def parse_aemo_mms_csv(
    content: str,
    table_set: AEMOTableSet | None = None,
    namespace_filter: list[str] | None = None,
    skip_records: bool = False,
    url: str | None = None,
    values_only: bool = False,
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
            logger.info(f"Skipping row, invalid type: {record_type}")
            continue

        # new table set
        # @TODO switch to match
        match record_type:
            case "C":
                # @TODO csv meta stored in table
                if table_current:
                    table_set.add_table(table_current, values_only=values_only)

            # new table
            case "I":
                if table_current:
                    table_set.add_table(table_current, values_only=values_only)

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
                    url_source=url,
                )

            # new record
            case "D":
                if skip_records:
                    continue

                if not table_current:
                    logger.error("Have a record but not currently in a table")
                    continue

                values = row[4:]

                if len(values) != len(table_current.fieldnames):
                    logger.error("Malformed AEMO csv - length mismatch between records and fields")
                    continue

                record = dict(zip(table_current.fieldnames, values, strict=True))

                for field, fieldvalue in record.items():
                    if field in MMS_DUID_FIELDS:
                        fieldvalue_parsed = normalize_duid(fieldvalue)
                        record[field] = fieldvalue_parsed

                table_current.add_record(record, values_only=values_only)

            case _:
                logger.error(f"Invalid AEMO record type: {record_type}")

    return table_set


async def parse_aemo_url(
    url: str, table_set: AEMOTableSet | None = None, skip_records: bool = False, values_only: bool = False
) -> AEMOTableSet:
    """Parse a single AEMO URL into an AEMOTableSet"""

    if not table_set:
        table_set = AEMOTableSet()

    try:
        csv_content = await url_downloader(url)
    except Exception as e:
        raise Exception(f"Could not fetch AEMO url {url}: {e}") from None

    if not csv_content:
        raise Exception(f"Could not parse URL: {url}")

    csv_content_decoded = csv_content.decode("utf-8")
    table_set = parse_aemo_mms_csv(csv_content_decoded, table_set, skip_records=skip_records, url=url, values_only=values_only)

    # Count number of records
    total_records = 0

    for table in table_set.tables:
        total_records += len(table.records)

    logger.info(f"Parsed {total_records} records")

    return table_set


def parse_aemo_file(file: str, table_set: AEMOTableSet | None = None, values_only: bool = False) -> AEMOTableSet:
    """Parses a local AEMO file"""
    if not table_set:
        table_set = AEMOTableSet()

    file_path = Path(file)

    if not file_path.is_file():
        raise Exception(f"Not a file {file_path}")

    if file_path.suffix.lower() != ".csv":
        raise Exception(f"Not a CSV file {file_path}")

    with file_path.open() as fh:
        table_set = parse_aemo_mms_csv(fh.read(), table_set=table_set, values_only=values_only)

    return table_set


# debug entry point
if __name__ == "__main__":
    # @TODO parse into MMS schema
    # url = "https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_20220612.zip"
    url = "https://nemweb.com.au/Reports/ARCHIVE/TradingIS_Reports/PUBLIC_TRADINGIS_20210620_20210626.zip"
    # parse_aemo_url_optimized(url)

    # controller_returns = store_aemo_tableset(r)
