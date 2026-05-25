"""QR-утилиты без зависимости от tkinter."""
import io
import os
import zipfile

import qrcode
from PIL import Image, ImageDraw, ImageFont


def create_qr_image(data: str, caption: str = "", box_size: int = 10) -> Image.Image:
    """Генерирует QR-код с опциональной подписью снизу."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if caption.strip():
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        new_img = Image.new("RGB", (img.width, img.height + text_height + 20), "white")
        new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text(
            ((img.width - text_width) // 2, img.height + 10),
            caption,
            fill="black",
            font=font,
        )
        img = new_img

    return img


def qr_to_bytes(data: str, caption: str = "", box_size: int = 10) -> bytes:
    """Возвращает PNG-байты QR-кода."""
    img = create_qr_image(data, caption, box_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def batch_qr_zip(lines: list[str], box_size: int = 10) -> bytes:
    """Генерирует ZIP с QR-кодами для каждой строки из списка."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, line in enumerate(lines, start=1):
            data = line.strip()
            if not data:
                continue
            caption = f"QR {idx}"
            png = qr_to_bytes(data, caption, box_size)
            zf.writestr(f"qr_{idx}.png", png)
    return buf.getvalue()
