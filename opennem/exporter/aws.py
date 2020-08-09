import logging
import os

from smart_open import open

logger = logging.getLogger(__name__)

S3_EXPORT_DEFAULT_BUCKET = "s3://data.opennem.org.au/v3/"

UPLOAD_ARGS = {
    "ContentType": "application/json",
}


def write_to_s3(file_path: str, data: str) -> int:
    """
        Write data to an s3 path
    """
    s3_save_path = os.path.join(S3_EXPORT_DEFAULT_BUCKET, file_path)
    write_count = 0

    with open(
        s3_save_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        write_count = fh.write(data)

    logger.info("Wrote {} to {}".format(len(data), s3_save_path))

    return write_count
