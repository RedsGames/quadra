"""Тесты для QR-модуля."""
import io
import zipfile
import pytest
from PIL import Image
from src.qr_module.qr_utils import create_qr_image, qr_to_bytes, batch_qr_zip


def test_create_qr_image_returns_pil_image():
    img = create_qr_image("https://redsgames.ru")
    assert isinstance(img, Image.Image)


def test_create_qr_image_with_caption():
    img_no_caption = create_qr_image("test")
    img_with_caption = create_qr_image("test", caption="Подпись")
    # С подписью изображение выше
    assert img_with_caption.height > img_no_caption.height


def test_create_qr_image_size_affects_output():
    img_small = create_qr_image("test", box_size=5)
    img_large = create_qr_image("test", box_size=15)
    assert img_large.width > img_small.width


def test_qr_to_bytes_returns_png():
    png = qr_to_bytes("https://example.com")
    # PNG файлы начинаются с сигнатуры \x89PNG
    assert png[:4] == b'\x89PNG'


def test_qr_to_bytes_is_valid_image():
    png = qr_to_bytes("hello world", caption="Тест", box_size=8)
    img = Image.open(io.BytesIO(png))
    assert img.format == "PNG"


def test_batch_qr_zip_returns_zip():
    lines = ["https://site1.ru", "https://site2.ru", "https://site3.ru"]
    zip_bytes = batch_qr_zip(lines)
    assert zip_bytes[:2] == b'PK'  # ZIP сигнатура


def test_batch_qr_zip_correct_file_count():
    lines = ["link1", "link2", "link3"]
    zip_bytes = batch_qr_zip(lines)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert len(zf.namelist()) == 3


def test_batch_qr_zip_skips_empty_lines():
    lines = ["link1", "", "link3", "  "]
    zip_bytes = batch_qr_zip(lines)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert len(zf.namelist()) == 2


def test_batch_qr_zip_file_names():
    lines = ["a", "b"]
    zip_bytes = batch_qr_zip(lines)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "qr_1.png" in names
        assert "qr_2.png" in names
