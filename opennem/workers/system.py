""" System worker for admin tasks """

import logging
import os
import time
from glob import glob
from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir

from opennem import settings
from opennem.core.profiler import profile_task

logger = logging.getLogger("opennem.workers.system")

CLEAN_OLDER_THAN_HOURS = 2


@profile_task(send_slack=True)
def clean_tmp_dir(dry_run: bool = False) -> None:
    """Cleans up the temp directory for files older than CLEAN_OLDER_THAN_HOURS hours"""
    tmp_dir = Path(gettempdir())
    now_epoch = time.time()

    logger.debug(f"Temp directory: {tmp_dir} running at {now_epoch}")

    if not tmp_dir.is_dir():
        raise Exception(f"Not a directory: {tmp_dir}")

    if not settings.tmp_file_prefix:
        raise Exception("No tmp file prefix")

    for dir_entry in glob(f"{str(tmp_dir)}/*"):
        dir_entry_path = Path(dir_entry)

        if dir_entry_path.name.startswith(settings.tmp_file_prefix):
            mtime = os.stat(dir_entry_path).st_mtime

            if mtime >= now_epoch - (CLEAN_OLDER_THAN_HOURS * 3600):
                logger.info(f"Keeping: {dir_entry_path} - {mtime}")
                continue

            logger.info(f"Will remove: {dir_entry_path}")

            if dry_run:
                continue

            try:
                rmtree(dir_entry_path)
            except Exception as e:
                logger.error(f"Error removing {dir_entry_path}: {e}")


if __name__ == "__main__":
    clean_tmp_dir(dry_run=True)
