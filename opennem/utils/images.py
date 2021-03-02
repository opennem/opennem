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
    img = img.resize((10, 10), Image.ANTIALIAS)
    img = img.convert("L")

    pixel_data = list(img.getdata())
    avg_pixel = sum(pixel_data) / len(pixel_data)
    bits = "".join(["1" if (px >= avg_pixel) else "0" for px in pixel_data])
    hex_representation = str(hex(int(bits, 2)))[2:][::-1].upper()

    return hex_representation
