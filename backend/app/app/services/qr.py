"""QR code generation."""

import base64
import io

import qrcode

from app.config import get_settings

settings = get_settings()


def generate_qr_code_data_url(token: str) -> tuple[str, str]:
    qr_url = f"{settings.frontend_url}/customer/{token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return qr_url, f"data:image/png;base64,{b64}"
