import io
import logging
import os

logger = logging.getLogger(__name__)

LOCAL_DIR_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")

if not os.path.exists(LOCAL_DIR_PATH):
    raise Exception("Folder {} does not exist".format(LOCAL_DIR_PATH))


def write_to_local(file_path, data):
    save_file_path = os.path.join(LOCAL_DIR_PATH, file_path)

    if type(data) is io.StringIO:
        data = data.getvalue()

    with open(save_file_path, "w") as fh:
        fh.write(data)

    logger.info("Wrote {} to {}".format(len(data), save_file_path))
