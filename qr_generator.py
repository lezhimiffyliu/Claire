"""
QR Code Generator - Generate QR codes for mobile upload URLs.

Uses the qrcode library with PIL for image generation.
"""

from io import BytesIO
from typing import Optional

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer


def get_upload_url(upload_token: str, app_url: str) -> str:
    """
    Get the full upload URL for mobile scanning.

    Args:
        upload_token: Raw token from generate_upload_token()
        app_url: Base URL of the app (e.g., https://claire.app)

    Returns:
        Full URL like https://claire.app/upload?t=abc123...
    """
    # Ensure no trailing slash
    base_url = app_url.rstrip("/")
    return f"{base_url}/upload?t={upload_token}"


def generate_qr_code(
    upload_token: str,
    app_url: str,
    size: int = 200,
    border: int = 2,
) -> bytes:
    """
    Generate a QR code PNG for the upload URL.

    Args:
        upload_token: Raw token from generate_upload_token()
        app_url: Base URL of the app
        size: Target size in pixels (approximate)
        border: Border width in modules

    Returns:
        PNG image bytes
    """
    url = get_upload_url(upload_token, app_url)

    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-size based on data
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate styled image with rounded corners
    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
        )
    except Exception:
        # Fallback to basic image if styling fails
        img = qr.make_image(fill_color="black", back_color="white")

    # Resize to target size
    img = img.resize((size, size))

    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


def generate_qr_code_simple(url: str, size: int = 200) -> bytes:
    """
    Generate a simple QR code for any URL.

    Args:
        url: Full URL to encode
        size: Target size in pixels

    Returns:
        PNG image bytes
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()
