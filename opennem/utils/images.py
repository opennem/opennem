from io import BytesIO

from PIL import Image


def img_to_buffer(img: Image):
    buf = BytesIO()

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    img.save(buf, format="JPEG")

    return buf.getbuffer()
