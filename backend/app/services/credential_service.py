"""Encryption helpers for credentials stored in integration metadata."""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.models.integration import Integration

logger = logging.getLogger("uvicorn")


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
    """Resolve SMTP settings from the business's active email integration."""
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
    if (
        settings.ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX
        and settings.MAIL_USERNAME
        and settings.MAIL_PASSWORD
    ):
        logger.warning(
            "[SANDBOX] Using explicitly enabled global email credentials for business %s",
            business_id,
        )
        return {
            "email": settings.MAIL_USERNAME,
            "password": settings.MAIL_PASSWORD,
            "smtp_host": settings.MAIL_SERVER,
            "smtp_port": settings.MAIL_PORT,
        }
    return None


def get_sandbox_channel_credentials(platform: str):
    """Return global channel credentials only under explicit sandbox opt-in."""
    if not settings.ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX:
        return None
    normalized = (platform or "").lower()
    credentials = None
    if normalized in {"facebook", "instagram"} and settings.FACEBOOK_PAGE_ACCESS_TOKEN:
        credentials = {
            "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
            "metadata": {"page_id": settings.FACEBOOK_PAGE_ID},
        }
    elif normalized == "whatsapp" and settings.WHATSAPP_ACCESS_TOKEN:
        credentials = {
            "access_token": settings.WHATSAPP_ACCESS_TOKEN,
            "metadata": {"phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID},
        }
    if credentials:
        logger.warning(
            "[SANDBOX] Using explicitly enabled global credentials for %s",
            normalized,
        )
    return credentials
