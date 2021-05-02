"""OpenNEM AEMO MMS Importer

Imports MMS data sets for any range into a local database schema

See also: mirror_mms.sh to dodwnload archives
"""


from pathlib import Path
from typing import List

import click

MMA_PATH = Path(__file__).parent / "data" / "mms"


def find_available_mms_sets() -> List[str]:
    pass


# debug and cli entrypoint
if __name__ == "__main__":
    pass
