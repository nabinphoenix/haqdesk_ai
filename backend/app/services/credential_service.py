"""Encryption helpers for credentials stored in integration metadata."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.models.integration import Integration


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    if not value:
        raise ValueError("Cannot encrypt an empty secret")
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    if not value:
        raise ValueError("Encrypted secret is missing")
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored credential cannot be decrypted") from exc


def get_business_email_credentials(db, business_id: int):
    """Resolve per-business SMTP settings, preserving TechSuru's env fallback."""
    integration = db.query(Integration).filter(
        Integration.business_id == business_id,
        Integration.platform == "email",
        Integration.status == "active",
    ).first()
    if integration:
        metadata = integration.metadata_json or {}
        encrypted = metadata.get("password_encrypted")
        if encrypted:
            return {
                "email": metadata.get("email") or integration.page_id,
                "password": decrypt_secret(encrypted),
                "smtp_host": metadata.get("smtp_host", "smtp.gmail.com"),
                "smtp_port": int(metadata.get("smtp_port", 587)),
            }
    if business_id == 1 and settings.TECHSURU_IMAP_EMAIL:
        return {
            "email": settings.TECHSURU_IMAP_EMAIL,
            "password": settings.TECHSURU_IMAP_PASSWORD,
            "smtp_host": settings.MAIL_SERVER,
            "smtp_port": settings.MAIL_PORT,
        }
    return None
