import io
import logging
from os import makedirs
from pathlib import Path

from opennem.settings import settings

logger = logging.getLogger(__name__)


def write_to_local(file_path, data):
    save_folder = settings.static_folder_path

    save_file_path = Path(save_folder) / file_path.lstrip("/")

    dir_path = save_file_path.resolve().parent

    if not dir_path.is_dir():
        makedirs(dir_path)

    if type(data) is io.StringIO:
        data = data.getvalue()

    bytes_written = 0

    with open(save_file_path, "w") as fh:
        bytes_written += fh.write(data)

    print("Wrote {} to {}".format(bytes_written, save_file_path))
