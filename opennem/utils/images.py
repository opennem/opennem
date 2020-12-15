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
