#!/usr/bin/env python
"""OpenNEM AEMO MMS Importer

Imports MMS data sets for any range into a local database schema

See also: mirror_mms.sh to dodwnload archives
"""

import gc
import logging
from pathlib import Path
from typing import List

import click

from opennem.settings import settings  # noq

logger = logging.getLogger("opennem.mms")

MMA_PATH = Path(__file__).parent / "data" / "mms"


def find_available_mms_sets() -> List[str]:
    pass


@click.command()
# @click.option("--purge", is_flag=True, help="Purge unmapped views")
def main() -> None:
    pass


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
