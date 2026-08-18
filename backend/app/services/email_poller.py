import imaplib
import email
import asyncio
from email.header import decode_header
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.integration import Integration
from app.services.webhook_service import process_incoming_message_in_background
from app.services.credential_service import decrypt_secret

logger = logging.getLogger("uvicorn")


def decode_str(value):
    """Decode email header string."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result += part.decode(charset or "utf-8", errors="replace")
            except Exception:
                result += part.decode("utf-8", errors="replace")
        else:
            result += part
    return result.strip()


def get_email_body(msg) -> str:
    """Extract clean readable text from email, strip HTML tags."""
    plain_text = ""
    html_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if content_type == "text/plain":
                try:
                    plain_text = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
            elif content_type == "text/html" and not plain_text:
                try:
                    html_text = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
    else:
        content_type = msg.get_content_type()
        try:
            raw = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
            if content_type == "text/html":
                html_text = raw
            else:
                plain_text = raw
        except Exception:
            pass

    # Prefer plain text
    if plain_text:
        return plain_text.strip()

    # Fall back to HTML — strip all tags and clean up whitespace
    if html_text:
        # Remove script and style blocks entirely
        html_text = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        # Remove all HTML tags
        html_text = re.sub(r'<[^>]+>', ' ', html_text)
        # Decode HTML entities
        html_text = html_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        # Collapse whitespace
        html_text = re.sub(r'\s+', ' ', html_text).strip()
        return html_text

    return ""


def get_email_attachments(msg) -> list:
    """Extract and save file attachments from email. Returns list of {filename, path, content_type}."""
    attachments = []
    if not msg.is_multipart():
        return attachments

    upload_dir = "uploads/attachments"
    os.makedirs(upload_dir, exist_ok=True)

    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        if "attachment" not in disposition:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        # Decode filename if encoded
        filename = decode_str(filename)
        if not filename:
            continue

        try:
            file_data = part.get_payload(decode=True)
            if not file_data:
                continue

            file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
            unique_filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, "wb") as f:
                f.write(file_data)

            attachments.append({
                "filename": filename,
                "path": file_path,
                "content_type": part.get_content_type() or "application/octet-stream",
            })
        except Exception:
            continue

    return attachments


def poll_emails_for_business(
    business_id: int,
    imap_email: str,
    imap_password: str,
    imap_host: str = None,
    imap_port: int = None,
):
    """Connect to Gmail IMAP and fetch unread emails, save as messages."""
    db: Session = SessionLocal()
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL(
            imap_host or settings.TECHSURU_IMAP_HOST,
            imap_port or settings.TECHSURU_IMAP_PORT,
        )
        mail.login(imap_email, imap_password)
        mail.select("inbox")

        # Search for unread emails only
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            mail.logout()
            db.close()
            return

        email_ids = messages[0].split()
        logger.info(f"[EMAIL POLL] Found {len(email_ids)} unread email(s) for business {business_id}")

        for email_id in email_ids:
            try:
                # Fetch the email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract fields
                sender_email = email.utils.parseaddr(msg.get("From", ""))[1].lower()
                sender_name = decode_str(email.utils.parseaddr(msg.get("From", ""))[0]) or sender_email
                subject = decode_str(msg.get("Subject", "(No Subject)"))
                body = get_email_body(msg)
                message_id = msg.get("Message-ID", f"email_{email_id.decode()}")

                if not body:
                    body = f"[Email: {subject}]"

                # Skip emails from self (avoid loop)
                if sender_email == imap_email.lower():
                    continue

                # Skip automated notification emails — only process real customer emails
                SKIP_SENDERS = [
                    "no-reply", "noreply", "donotreply", "mailer-daemon",
                    "notification", "notifications", "notify",
                    "instagram", "facebook", "google", "youtube",
                    "accounts-noreply", "security", "support@google",
                    "mail-noreply", "facebookmail.com", "insta",
                ]

                SKIP_SUBJECTS = [
                    "security alert", "2-step verification", "sign in attempt",
                    "unread message", "catch up", "missed", "happening on instagram",
                    "performance report", "your profile", "terms of service",
                    "privacy settings", "new features", "account activity",
                    "notification", "verify your", "confirm your",
                ]

                sender_lower = sender_email.lower()
                subject_lower = subject.lower()

                # Skip if sender matches any notification pattern
                if any(skip in sender_lower for skip in SKIP_SENDERS):
                    logger.info(f"[EMAIL POLL] Skipping notification email from {sender_email}")
                    mail.store(email_id, "+FLAGS", "\\Seen")
                    continue

                # Skip if subject matches notification patterns
                if any(skip in subject_lower for skip in SKIP_SUBJECTS):
                    logger.info(f"[EMAIL POLL] Skipping notification email: {subject[:50]}")
                    mail.store(email_id, "+FLAGS", "\\Seen")
                    continue

                # Skip if already processed (check by message_id in content)
                existing = db.query(Message).filter(
                    Message.platform == "email",
                    Message.content.contains(message_id)
                ).first()
                if existing:
                    continue

                logger.info(f"[EMAIL POLL] New email from {sender_email}: {subject[:50]}")

                # Find or create customer
                customer = db.query(Customer).filter(
                    Customer.business_id == business_id,
                    Customer.platform_user_id == sender_email,
                    Customer.platform == "email"
                ).first()

                if not customer:
                    customer = Customer(
                        platform="email",
                        platform_user_id=sender_email,
                        display_name=sender_name,
                        business_id=business_id,
                        is_merged=False,
                    )
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)

                # Find or create conversation
                conversation = db.query(Conversation).filter(
                    Conversation.customer_id == customer.id,
                    Conversation.business_id == business_id,
                ).order_by(Conversation.created_at.desc()).first()

                if conversation:
                    # Auto-restore if it was soft-deleted
                    if conversation.is_deleted:
                        conversation.is_deleted = False
                        conversation.deleted_at = None
                        conversation.status = "open"
                        db.commit()
                        logger.info(f"[EMAIL POLL] Auto-restored deleted conversation {conversation.id} — customer emailed again")
                    # Reopen if closed/resolved
                    elif conversation.status in ["closed", "resolved"]:
                        conversation.status = "open"
                        db.commit()
                        logger.info(f"[EMAIL POLL] Reopened closed/resolved conversation {conversation.id} — customer emailed again")
                else:
                    conversation = Conversation(
                        business_id=business_id,
                        customer_id=customer.id,
                        status="open",
                        priority="medium",
                    )
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)

                # Save message — include message_id in content for dedup
                full_content = f"{body}\n\n[msg-id:{message_id}]"
                new_message = Message(
                    conversation_id=conversation.id,
                    sender_type="customer",
                    sender_id=None,
                    content=f"📧 {subject}\n\nFrom: {sender_email}\n\n{body}\n\n[msg-id:{message_id}]",
                    platform="email",
                    message_type="text",
                )
                db.add(new_message)
                db.commit()

                # Mark email as read in Gmail
                mail.store(email_id, "+FLAGS", "\\Seen")

                logger.info(f"[EMAIL POLL] Saved email from {sender_email} as message {new_message.id}")

                # Save email attachments as separate messages
                email_attachments = get_email_attachments(msg)
                for att in email_attachments:
                    filename = att['filename']
                    file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
                    
                    image_exts = {"jpg", "jpeg", "png", "gif", "webp"}
                    video_exts = {"mp4", "mov", "avi"}
                    if file_ext in image_exts:
                        att_message_type = "image"
                    elif file_ext in video_exts:
                        att_message_type = "video"
                    else:
                        att_message_type = "file"

                    att_message = Message(
                        conversation_id=conversation.id,
                        sender_type="customer",
                        sender_id=None,
                        content=f"/uploads/attachments/{os.path.basename(att['path'])}",
                        platform="email",
                        message_type=att_message_type,
                        ai_metadata={"filename": filename}
                    )
                    db.add(att_message)
                    db.commit()
                    logger.info(f"[EMAIL POLL] Saved attachment '{filename}' as message {att_message.id}")

                # Use the same mode-aware RAG/dispatch pipeline as Messenger
                # and Instagram. In auto mode it sends via SMTP; in review
                # mode it creates an AI suggestion for an agent.
                logger.info(
                    "[EMAIL POLL] Triggering AI pipeline for message %s "
                    "(conversation=%s, business=%s)",
                    new_message.id,
                    conversation.id,
                    business_id,
                )
                try:
                    # asyncio.run() creates a fresh event loop, safe to call
                    # from a background thread that has no running loop.
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(
                            process_incoming_message_in_background(
                                new_message.id,
                                conversation.id,
                                body,
                                business_id,
                                reply_subject=f"Re: {subject}",
                            )
                        )
                    finally:
                        loop.close()
                except Exception as pipeline_err:
                    logger.exception(
                        "[EMAIL POLL] AI pipeline failed for message %s: %s",
                        new_message.id,
                        pipeline_err,
                    )

            except Exception as e:
                logger.exception(
                    "[EMAIL POLL] Error processing email %s: %s",
                    email_id,
                    e,
                )
                db.rollback()
                continue

        mail.logout()

    except imaplib.IMAP4.error as e:
        logger.error(f"[EMAIL POLL] IMAP connection failed: {e}")
    except Exception as e:
        logger.error(f"[EMAIL POLL] Unexpected error: {e}")
    finally:
        db.close()


def build_email_poll_configs(db):
    """Build isolated polling configurations from active integrations."""
    integrations = db.query(Integration).filter(
        Integration.platform == "email",
        Integration.status == "active",
    ).all()
    configs = []
    for integration in integrations:
        metadata = integration.metadata_json or {}
        try:
            configs.append({
                "business_id": integration.business_id,
                "imap_email": metadata.get("email") or integration.page_id,
                "imap_password": decrypt_secret(
                    metadata.get("password_encrypted")
                ),
                "imap_host": metadata.get("imap_host", "imap.gmail.com"),
                "imap_port": int(metadata.get("imap_port", 993)),
            })
        except Exception as exc:
            logger.error(
                "[EMAIL POLL] Invalid stored email integration %s: %s",
                integration.id,
                exc,
            )
    return configs


def run_email_poll():
    """Poll all active business email integrations."""
    db = SessionLocal()
    try:
        configs = build_email_poll_configs(db)
    finally:
        db.close()

    for config in configs:
        poll_emails_for_business(**config)
