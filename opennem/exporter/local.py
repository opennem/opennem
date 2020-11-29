import io
import logging
from io import BytesIO, StringIO
from os import makedirs
from pathlib import Path
from typing import Optional, Union

from opennem.settings import settings
from opennem.utils.mime import decode_bytes

logger = logging.getLogger(__name__)


def write_to_local(
    file_path: str, data: Union[StringIO, bytes, BytesIO, str]
) -> int:
    save_folder = settings.static_folder_path

    save_file_path = Path(save_folder) / file_path.lstrip("/")

    dir_path = save_file_path.resolve().parent

    if not dir_path.is_dir():
        makedirs(dir_path)

    write_data: Optional[str] = None

    if isinstance(data, StringIO):
        write_data = data.getvalue()
    elif isinstance(data, BytesIO):
        write_data = decode_bytes(data.getvalue())
    elif isinstance(data, bytes):
        write_data = decode_bytes(data)
    elif data:
        write_data = data

    bytes_written = 0

    if not write_data:
        logger.info("No data to write to {}".format(file_path))
        return 0

    with open(save_file_path, "w") as fh:
        bytes_written += fh.write(write_data)

    logger.info("Wrote {} to {}".format(bytes_written, save_file_path))

    return bytes_written
