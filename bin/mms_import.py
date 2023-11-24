#!/usr/bin/env python
"""OpenNEM AEMO MMS Importer

Imports MMS data sets for any range into a local database schema

See also: mirror_mms.sh to dodwnload archives
"""

import gc
import logging

# import mmap
import re
from pathlib import Path

import click

from opennem.core.parsers.aemo.mms import AEMOTableSchema, parse_aemo_mms_csv
from opennem.db import get_database_engine
from opennem.db.models import mms
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.settings import settings  # noq
from opennem.utils.handlers import open

logger = logging.getLogger("opennem.mms")

MMA_PATH = Path(__file__).parent / "data" / "mms"


def find_available_mms_sets() -> list[str]:
    pass


MMS_MODELS = [getattr(mms, item) for item in dir(mms) if hasattr(getattr(mms, item), "__tablename__")]


def get_mms_model(table: AEMOTableSchema) -> mms.Base | None:
    table_lookup = list(
        filter(
            lambda x: x.__tablename__ == table.full_name or x.__tablename__ == table.name,
            MMS_MODELS,
        )
    )

    if not table_lookup:
        logger.error(f"Could not find ORM model for table {table.full_name}")
        return None

    return table_lookup.pop()


def store_mms_table(table: AEMOTableSchema) -> int:
    if not table.name:
        logger.error(f"Table has no name!: {table}")
        return 0

    # Get the table ORM model
    table_schema = get_mms_model(table)

    if not table_schema:
        logger.error(f"No table ORM schema for table name {table.name}")
        return 0

    # update all non-primary key fields. get them dynamically.
    update_fields = [i.name for i in table_schema.__table__.columns if not i.primary_key]  # type: ignore

    records_to_store = table.records

    sql_query = ""

    try:
        sql_query = build_insert_query(table_schema, update_fields)
    except Exception as e:
        logger.error(e)
        return 0

    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()

    csv_content = ""

    try:
        csv_content = generate_csv_from_records(
            table_schema,
            records_to_store,
            column_names=list(records_to_store[0].keys()),
        )
    except Exception as e:
        logger.error(e)
        return 0

    if not csv_content:
        return 0

    logger.debug(csv_content.getvalue().splitlines()[:2])

    cursor.copy_expert(sql_query, csv_content)
    conn.commit()

    logger.info(f"{table.full_name}: Inserted {len(records_to_store)} records")

    return len(records_to_store)


def import_file(filepath: Path, namespace: str | None = None) -> None:
    content = None

    with open(filepath, mode="r") as fh:
        # with mmap.mmap(fh.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_obj:
        content = fh.read()

    logger.info(f"Reading file: {filepath}")

    if namespace:
        ts = parse_aemo_mms_csv(content, namespace_filter=[namespace])
    else:
        ts = parse_aemo_mms_csv(content)

    logger.debug(f"Loaded {len(ts.table_names)} tables")

    for table in ts.tables:
        if namespace and table.namespace != namespace:
            continue

        logger.debug(f"Storing table: {table.namespace} {table.full_name}")

        try:
            store_mms_table(table)
        except Exception as e:
            logger.error(f"Could not store for table: {table.full_name}: {e}")
            raise e


def import_directory(mms_dir: str, namespace: str | None = None) -> None:
    mmsdir = Path(mms_dir)

    if not mmsdir.is_dir():
        raise Exception(f"Not a directory: {mms_dir}")

    for f in mmsdir.glob("*.zip"):
        import_file(f, namespace=namespace)


@click.command()
@click.argument("filepath", type=str, required=True)
@click.option("--namespace", type=str, required=False)
def cmd_import_file(filepath: Path, namespace: str | None = None) -> None:
    import_file(filepath=filepath, namespace=namespace)


@click.command()
@click.argument("mms_dir", type=str, required=True)
@click.option("--namespace", type=str, required=False)
def cmd_import_directory(mms_dir: str, namespace: str | None = None) -> None:
    mmsdir = Path(mms_dir)

    if not mmsdir.is_dir():
        raise Exception(f"Not a directory: {mms_dir}")

    for f in mmsdir.glob("*.zip"):
        import_file(f, namespace=namespace)


@click.command()
@click.option("--namespace", type=str, required=False)
@click.option("--debug", is_flag=True, default=False)
def all(namespace: str | None = None, debug: bool | None = False) -> None:
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("opennem.pipelines.bulk_insert").setLevel(logging.INFO)
    logger.setLevel(logging.INFO)

    mms_data_dir = Path("data/mms/")

    logger.info(f"Importing from {mms_data_dir}")

    if namespace:
        logger.info(f"Filtering to namespace: {namespace}")

    if debug:
        logger.setLevel(logging.DEBUG)

    if not mms_data_dir.is_dir():
        raise Exception(f"Not a directory: {mms_data_dir}")

    for _dir in sorted(mms_data_dir.iterdir()):
        if not re.match(r"^\d{4}$", _dir.name):
            continue

        for _dir_month in sorted(_dir.iterdir()):
            if not re.match(r"^MMSDM_\d{4}_\d{2}", _dir_month.name):
                continue

            mms_path = _dir_month / "MMSDM_Historical_Data_SQLLoader/DATA/"

            if not mms_path.is_dir():
                logger.warn(f"Have mms folder with no data: {_dir_month}")
                continue

            logger.info(f"Running import on: {mms_path}")

            import_directory(str(mms_path), namespace=namespace)


@click.group()
def main() -> None:
    pass


main.add_command(all)
main.add_command(cmd_import_directory, name="dir")
main.add_command(cmd_import_file, name="file")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)

        if settings.debug:
            import traceback

            traceback.print_exc()

    finally:
        gc.collect()
