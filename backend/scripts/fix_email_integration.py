"""
One-off migration: fix business_id=1 email integration.

Updates integration id=51 (info.haqdesk.ai@gmail.com) to point to
techsuru1@gmail.com so the email poller picks up the correct inbox.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.integration import Integration
from app.services.credential_service import encrypt_secret
from app.core.config import settings


def run():
    if not settings.TECHSURU_IMAP_EMAIL:
        print("ERROR: TECHSURU_IMAP_EMAIL is not set in .env")
        sys.exit(1)
    if not settings.TECHSURU_IMAP_PASSWORD:
        print("ERROR: TECHSURU_IMAP_PASSWORD is not set in .env")
        sys.exit(1)

    db = SessionLocal()
    try:
        integration = db.query(Integration).filter(
            Integration.id == 51
        ).first()

        if not integration:
            # Try finding by business_id=1 + platform=email
            integration = db.query(Integration).filter(
                Integration.business_id == 1,
                Integration.platform == "email",
            ).first()

        if not integration:
            print("ERROR: Could not find email integration for business_id=1")
            sys.exit(1)

        old_email = integration.page_id
        new_email = settings.TECHSURU_IMAP_EMAIL.lower()

        print(f"Found integration id={integration.id}")
        print(f"  Current email : {old_email}")
        print(f"  New email     : {new_email}")

        integration.page_id = new_email
        integration.page_name = new_email
        integration.access_token = "encrypted-app-password"
        integration.metadata_json = {
            "email": new_email,
            "password_encrypted": encrypt_secret(settings.TECHSURU_IMAP_PASSWORD),
            "imap_host": settings.TECHSURU_IMAP_HOST,
            "imap_port": settings.TECHSURU_IMAP_PORT,
            "smtp_host": settings.MAIL_SERVER,
            "smtp_port": settings.MAIL_PORT,
            "credential_type": "gmail_app_password",
        }
        integration.status = "active"
        db.commit()
        print(f"\n✅ Integration updated successfully → {new_email}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
