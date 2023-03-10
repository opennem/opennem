import csv
import logging
from datetime import datetime
from pathlib import Path

from opennem.api.photo.controllers import write_photo_to_s3
from opennem.core.loader import load_data
from opennem.core.photos.processor import get_image_from_web
from opennem.core.photos.schema import PhotoImportSchema
from opennem.db import SessionLocal
from opennem.db.models.opennem import Photo, Station
from opennem.utils.images import image_get_crypto_hash, img_to_buffer

logger = logging.getLogger("opennem.importer.photos")

# This can be read dynamically from the pydantic schema
# come to think of it no reason why a generic CSV->pydantic
# importer cannot be written
CSV_IMPORT_FORMAT_COLUMNS = [
    "network_id",
    "station_code",
    "is_primary",
    "image_url",
    "author",
    "author_link",
    "license",
    "license_link",
]


def get_import_photo_data(file_name: str = "photos.csv") -> list[PhotoImportSchema]:
    photo_file_path: Path = load_data("photos.csv", from_project=True, return_path=True)

    if not photo_file_path.is_file():
        raise Exception(f"Could not import photo file data: {str(photo_file_path)}")

    photo_records: list[PhotoImportSchema] = []

    with photo_file_path.open() as fh:
        # skip csv header
        fh.readline()

        csvreader = csv.DictReader(fh, fieldnames=CSV_IMPORT_FORMAT_COLUMNS)

        # Parse CSV records into schemas
        photo_records = [PhotoImportSchema(**i) for i in csvreader]

    return photo_records


def import_photos_from_fixtures() -> None:
    """Import photos to stations"""
    session = SessionLocal()
    photo_records = get_import_photo_data()

    for photo_record in photo_records:
        station = session.query(Station).filter(Station.code == photo_record.station_code).one_or_none()

        if not station:
            logger.error(f"Could not find station {photo_record.station_code}")
            continue

        img = get_image_from_web(photo_record.image_url)

        if not img:
            logger.error(f"No image for {photo_record.image_url}")
            continue

        hash_id = image_get_crypto_hash(img)[-8:]
        file_name = "{}_{}_{}.{}".format(hash_id, station.name.replace(" ", "_"), "original", "jpeg")

        photo = session.query(Photo).filter_by(hash_id=hash_id).one_or_none()

        if not photo:
            photo = Photo(
                hash_id=hash_id,
            )

        photo.name = file_name
        photo.width = img.size[0]
        photo.height = img.size[1]
        photo.original_url = photo_record.image_url
        photo.license_type = photo_record.license
        photo.license_link = photo_record.license_link
        photo.author = photo_record.author
        photo.author_link = photo_record.author_link

        if photo_record.is_primary:
            photo.is_primary = True

        photo.approved = True
        photo.approved_by = "opennem.importer.photos"
        photo.approved_at = datetime.now()

        img_buff = img_to_buffer(img)

        write_photo_to_s3(file_name, img_buff)

        if station:
            station.photos.append(photo)

        session.add(photo)

        if station:
            session.add(station)

        session.commit()


if __name__ == "__main__":
    import_photos_from_fixtures()
