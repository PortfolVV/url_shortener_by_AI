"""QR code generation.

SVG is used instead of PNG because it needs no Pillow dependency, scales
perfectly on the frontend and embeds directly into an ``<img>`` tag as a data
URI.
"""

import base64
import io

import qrcode
import qrcode.image.svg


def generate_qr_svg(data: str, box_size: int = 10, border: int = 4) -> bytes:
    """Render ``data`` as an SVG QR code and return raw bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buffer = io.BytesIO()
    image.save(buffer)
    return buffer.getvalue()


def generate_qr_data_uri(data: str) -> str:
    """Return a ``data:image/svg+xml;base64,...`` URI ready for the frontend."""
    svg = generate_qr_svg(data)
    encoded = base64.b64encode(svg).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
