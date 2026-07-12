import base64
import binascii

import cv2
import numpy as np


def decode_base64_image(image: str) -> np.ndarray:
    payload = image.split(",", 1)[1] if "," in image else image
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Image must be valid base64.") from exc

    buffer = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Image payload could not be decoded.")
    return frame
