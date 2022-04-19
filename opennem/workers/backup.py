""" OpenNEM Backup Scripts and Tools

Includes a worker that backs up the database to s3
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import urlparse

import boto3

from opennem import settings
from opennem.db import get_database_engine
from opennem.utils.dates import TODAY_NEM
from opennem.utils.security import get_random_string

logger = logging.getLogger("opennem.workers.backup")


class OpennemBackupException(Exception):
    pass


def run_timescaledb_restore(pre: bool = True) -> bool:
    """Run postgres pre-post restore commands"""

    engine = get_database_engine()

    query = "select timescaledb_post_restore();"

    if pre:
        query = "select timescaledb_pre_restore();"

    with engine.begin() as c:
        result = c.execute(query)

    print(result)

    return True


def run_pg_dump(dest_file: Path) -> Path:
    """Runs pg_dump to the destination file. Uses database from settings"""

    logger.debug("Will save db to {}".format(dest_file))

    pg_dump_cmd = [
        "pg_dump",
        "--dbname={}".format(settings.db_url),
        "-Fc",
        # "-j",  # jobs to run
        # "4",
        "-Z",  # compression level
        "7",
        "-f",
        dest_file,
    ]

    logger.debug(" ".join([str(i) for i in pg_dump_cmd]))

    try:
        with subprocess.Popen(
            pg_dump_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            logger.debug(proc.stdout.read())
            logger.error(proc.stderr.read())
            logger.debug(f"return: {proc.returncode}")

    except Exception as e:
        if "No such file or directory" in str(e):
            raise OpennemBackupException("Could not find command: {}".format(pg_dump_cmd[0]))
        raise OpennemBackupException(e)

    return dest_file


def upload_backup_to_s3(backup_path: Path) -> str:
    """Upload the backup file to s3"""

    if not backup_path.is_file():
        raise OpennemBackupException("Not a file: {}".format(backup_path))

    date_today = TODAY_NEM.strftime("%Y%M%d")
    backup_name = "{}_{}.db".format(urlparse(settings.db_url).path, date_today)
    s3_client = boto3.client("s3")

    logger.debug("Saving to {}".format(backup_name))

    s3_client.upload_file(str(backup_path), settings.backup_bucket_path, backup_name)

    return backup_name


def run_backup() -> str:
    _temp_folder = mkdtemp()
    dest_file = Path(_temp_folder) / "opennem_backup_{}.db".format(get_random_string())

    try:
        run_timescaledb_restore()
        backup_file = run_pg_dump(dest_file)
        backup_size = os.path.getsize(backup_file)

        if backup_size < 1:
            raise OpennemBackupException("Zero sized file at {}".format(backup_file))

        logger.info("Saved to {}".format(backup_file))

        s3_save_path = upload_backup_to_s3(dest_file)

        run_timescaledb_restore(pre=False)

        shutil.rmtree(_temp_folder, ignore_errors=True)

        return s3_save_path
    except Exception as e:
        logger.error(e)
        raise OpennemBackupException(e)
    finally:
        run_timescaledb_restore(pre=False)
        shutil.rmtree(_temp_folder, ignore_errors=True)


if __name__ == "__main__":
    run_backup()
