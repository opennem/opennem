import logging
import urllib
from typing import Dict
from urllib.parse import urljoin

from smart_open import open

from opennem.settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Support S3 URI's in urllib
urllib.parse.uses_netloc.append("s3")
urllib.parse.uses_relative.append("s3")


def get_upload_args(content_type: str = "application/json") -> Dict:
    return {"ContentType": content_type}


def write_to_s3(
    file_path: str, data: str, content_type: str = "application/json"
) -> int:
    """
        Write data to an s3 path
    """
    s3_save_path = urljoin(settings.s3_bucket_path, file_path)

    write_count = 0
    upload_args = get_upload_args(content_type)

    with open(
        s3_save_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=upload_args),
    ) as fh:
        write_count = fh.write(data)

    print("Wrote {} to {}".format(len(data), s3_save_path))

    return write_count
