import logging
import os
from io import BytesIO

import requests
from PIL import Image
from smart_open import open

logger = logging.getLogger(__name__)

S3_EXPORT_DEFAULT_BUCKET = "s3://photos.opennem.org.au/"


UPLOAD_ARGS = {
    "ContentType": "image/jpeg",
}


def write_photo_to_s3(file_path: str, data):
    # @TODO move this to aws.py
    s3_save_path = os.path.join(S3_EXPORT_DEFAULT_BUCKET, file_path)
    write_count = 0

    with open(
        s3_save_path,
        "wb",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        write_count = fh.write(data)

    logger.info("Wrote {} to {}".format(len(data), s3_save_path))

    return write_count


def photos_process():
    """"""
    pass
    # session = SessionLocal()

    # photos: List[Photo] = session.query(Photo).filter_by(processed=False).all()

    # for photo in photos:
    #     r = write_photo_to_s3(photo.name, photo.url)


def store_photo(photo_url: str):
    img = Image.open(requests.get(photo_url, stream=True).raw)

    save_bugger = BytesIO()
    img.save(save_bugger, format="JPEG")

    write_photo_to_s3("test.jpeg", data=save_bugger.getbuffer())


if __name__ == "__main__":
    photos_process()
