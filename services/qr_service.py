from __future__ import annotations

from io import BytesIO
from pathlib import Path

import qrcode


def qr_png_bytes(text: str, box_size: int = 8) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=box_size, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def save_qr_png(text: str, path: str | Path) -> None:
    Path(path).write_bytes(qr_png_bytes(text))

