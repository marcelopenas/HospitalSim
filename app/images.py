"""Bounded base64 transport for patient image BLOBs."""

import base64
import binascii
from pathlib import Path

MAX_IMAGE_BYTES = 65535
MAX_BASE64_LENGTH = ((MAX_IMAGE_BYTES + 2) // 3) * 4
DEFAULT_IMAGE = (
    Path(__file__)
    .with_name("assets")
    .joinpath("patient-default.png")
    .read_bytes()
)


def decode_image(value: str | None) -> bytes:
    if value is None:
        return DEFAULT_IMAGE
    try:
        image = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as cause:
        msg = "image_blob must be valid base64 without a data-URL prefix"
        raise ValueError(msg) from cause
    if not image or len(image) > MAX_IMAGE_BYTES:
        msg_0 = "image_blob must contain 1 to 65535 decoded bytes"
        raise ValueError(msg_0)
    png = image.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in image[-12:]
    jpeg = image.startswith(b"\xff\xd8\xff") and image.endswith(b"\xff\xd9")
    webp = image.startswith(b"RIFF") and image[8:12] == b"WEBP"
    if not (png or jpeg or webp):
        msg_1 = "image_blob must have PNG, JPEG, or WebP image headers"
        raise ValueError(msg_1)
    return image


def validate_image(value: str | None) -> str | None:
    decode_image(value)
    return value
