# Photo validation tests

import pytest
from fastapi import HTTPException

from app.api.v1.photos import detect_image_mime, validate_image


def test_detect_jpeg():
    assert detect_image_mime(b"\xff\xd8\xff\xe0" + b"\x00" * 20) == "image/jpeg"


def test_detect_png():
    assert detect_image_mime(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20) == "image/png"


def test_detect_webp():
    assert detect_image_mime(b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 20) == "image/webp"


def test_reject_invalid():
    with pytest.raises(HTTPException):
        detect_image_mime(b"not-an-image")


def test_reject_oversized():
    with pytest.raises(HTTPException):
        validate_image(b"\x00" * (21 * 1024 * 1024))
