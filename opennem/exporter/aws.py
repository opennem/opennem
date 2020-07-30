import logging
import os

from smart_open import open

logger = logging.getLogger(__name__)

S3_EXPORT_DEFAULT_BUCKET = "s3://data.opennem.org.au/v3/"

UPLOAD_ARGS = {
    "ContentType": "application/json",
}


def write_to_s3(file_path, data):
    s3_save_path = os.path.join(S3_EXPORT_DEFAULT_BUCKET, file_path)

    with open(
        s3_save_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        fh.write(data)

    logger.info("Wrote {} to {}".format(len(data), s3_save_path))
