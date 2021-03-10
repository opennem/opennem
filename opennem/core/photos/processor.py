import csv
import json
import logging
from typing import Optional
from urllib.parse import urlparse

from PIL import Image

from opennem.db import SessionLocal
from opennem.db.models.opennem import Photo, Station
from opennem.utils.http import http
from opennem.utils.images import image_get_crypto_hash, img_to_buffer

from .schema import PhotoImportSchema

logger = logging.getLogger(__name__)


def get_image_from_web(image_url: str) -> Image:
    """ Gets an image from an URL """
    img = None

    try:
        img = Image.open(http.get(image_url, stream=True).raw)
    except Exception:
        logger.error("Error parsing: %s", image_url)
        return None

    return img


def import_photo(photo: PhotoImportSchema):
    """ Imports a photo from a photo import schema """
    pass
