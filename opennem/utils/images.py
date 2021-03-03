from hashlib import md5
from io import BytesIO

from PIL import Image


def img_to_buffer(img: Image) -> memoryview:
    """
    Convert image and save as JPEG

    @TODO jpeg settings in opennem.settings

    """
    buf = BytesIO()

    # convert all to RGP
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    img.save(buf, format="JPEG")

    return buf.getbuffer()


def image_get_hash(img: Image) -> str:
    """Image hash based on content"""
    img = img.resize((10, 10), Image.ANTIALIAS)
    img = img.convert("L")

    pixel_data = list(img.getdata())
    avg_pixel = sum(pixel_data) / len(pixel_data)
    bits = "".join(["1" if (px >= avg_pixel) else "0" for px in pixel_data])
    hex_representation = str(hex(int(bits, 2)))[2:][::-1].upper()

    return hex_representation.lower()


def image_get_crypto_hash(img: Image, save_driver: str = "JPEG") -> str:
    """Get a cryptographic hash of an image"""
    img_hash = md5()

    # convert to RGB
    img_rgb = img.convert("RGB")

    with BytesIO() as memobj:
        img_rgb.save(memobj, save_driver)
        data = memobj.getvalue()
        img_hash.update(data)

    return img_hash.hexdigest()
