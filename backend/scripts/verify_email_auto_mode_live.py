"""Live SMTP -> IMAP ingestion -> RAG -> SMTP -> IMAP round-trip check."""

import email
import imaplib
import re
import sys
import time
from datetime import datetime
from email.header import decode_header
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.business import Business
from app.models.integration import Integration
from app.services.credential_service import decrypt_secret
from app.services.email_poller import run_email_poll
from app.services.email_service import send_email


def decoded(value):
    parts = []
    for item, charset in decode_header(value or ""):
        parts.append(
            item.decode(charset or "utf-8", errors="replace")
            if isinstance(item, bytes)
            else item
        )
    return "".join(parts)


def find_reply(subject):
    mail = imaplib.IMAP4_SSL(settings.MAIL_IMAP_HOST, settings.MAIL_IMAP_PORT)
    try:
        mail.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, "SUBJECT", f'"Re: {subject}"')
        if status != "OK" or not data[0]:
            return None
        latest_id = data[0].split()[-1]
        status, message_data = mail.fetch(latest_id, "(RFC822)")
        if status != "OK":
            return None
        parsed = email.message_from_bytes(message_data[0][1])
        html_body = None
        for part in parsed.walk():
            if part.get_content_type() == "text/html":
                html_body = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8",
                    errors="replace",
                )
                break
        return {
            "imap_id": latest_id.decode(),
            "subject": decoded(parsed.get("Subject")),
            "from": parsed.get("From"),
            "to": parsed.get("To"),
            "message_id": parsed.get("Message-ID"),
            "content_type": "text/html" if html_body else parsed.get_content_type(),
            "html_body": html_body,
            "rendered_text": re.sub(
                r"\n{3,}",
                "\n\n",
                re.sub(
                    r"<[^>]+>",
                    "\n",
                    (html_body or ""),
                ),
            ).strip(),
        }
    finally:
        mail.logout()


def email_test_context(business_id):
    db = SessionLocal()
    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        integration = db.query(Integration).filter(
            Integration.business_id == business_id,
            Integration.platform == "email",
            Integration.status == "active",
        ).first()
        if not business or not integration:
            raise RuntimeError("Business must have an active email integration")
        metadata = integration.metadata_json or {}
        return {
            "business_name": business.name or "Support Team",
            "email": metadata.get("email") or integration.page_id,
            "password": decrypt_secret(metadata.get("password_encrypted")),
        }
    finally:
        db.close()


def find_database_result(subject, business_id, sender_email):
    db = SessionLocal()
    try:
        customer = (
            db.query(Customer)
            .filter(
                Customer.business_id == business_id,
                Customer.platform == "email",
                Customer.platform_user_id == sender_email.lower(),
            )
            .first()
        )
        if not customer:
            return None
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.business_id == business_id,
                Conversation.customer_id == customer.id,
            )
            .order_by(Conversation.created_at.desc())
            .first()
        )
        if not conversation:
            return None
        incoming = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.sender_type == "customer",
                Message.content.contains(subject),
            )
            .order_by(Message.timestamp.desc())
            .first()
        )
        if not incoming:
            return None
        reply = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.sender_type == "agent",
                Message.timestamp >= incoming.timestamp,
            )
            .order_by(Message.timestamp.asc())
            .first()
        )
        return {
            "conversation_id": conversation.id,
            "incoming_message_id": incoming.id,
            "incoming_timestamp": incoming.timestamp.isoformat(),
            "reply_message_id": reply.id if reply else None,
            "reply_timestamp": reply.timestamp.isoformat() if reply else None,
            "reply_preview": reply.content[:200] if reply else None,
        }
    finally:
        db.close()


def main(business_id):
    context = email_test_context(business_id)
    marker = datetime.now().strftime("%Y%m%d-%H%M%S")
    subject = f"HaqDesk Auto Mode Live Test {marker}"
    body = (
        f"<p>Hello {context['business_name']} Support,</p>"
        "<p>I am planning to buy a laptop and have several questions:</p>"
        "<ol>"
        "<li>Is delivery available outside Kathmandu?</li>"
        "<li>How long does delivery usually take?</li>"
        "<li>Are there delivery charges?</li>"
        "<li>Can I choose a preferred delivery date and time?</li>"
        "<li>Can a family member receive it if I am unavailable?</li>"
        "</ol>"
        f"<p>Test marker: {marker}</p>"
    )
    print(f"TEST_SUBJECT={subject}")
    if not send_email(context["email"], subject, body):
        raise RuntimeError("Initial SMTP test email was not accepted")
    print("INITIAL_SMTP_ACCEPTED=true")

    database_result = None
    reply_result = None
    for attempt in range(1, 7):
        time.sleep(10)
        run_email_poll()
        database_result = find_database_result(
            subject, business_id, settings.MAIL_USERNAME
        )
        reply_result = find_reply(subject)
        print(
            f"attempt={attempt} database_reply={bool(database_result and database_result['reply_message_id'])} "
            f"imap_reply={bool(reply_result)}"
        )
        if database_result and database_result["reply_message_id"] and reply_result:
            break

    print(f"DATABASE_RESULT={database_result}")
    print(
        "IMAP_REPLY_METADATA="
        f"{dict(reply_result, html_body='<omitted>') if reply_result else None}"
    )
    if reply_result:
        print("RECEIVED_HTML_START")
        print(reply_result["html_body"])
        print("RECEIVED_HTML_END")
    if not database_result or not database_result["reply_message_id"]:
        raise RuntimeError("No AI reply was recorded after live email ingestion")
    if not reply_result:
        raise RuntimeError("AI reply was not found in the real recipient inbox")
    print("LIVE_EMAIL_AUTO_MODE_VERIFIED=true")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--business-id", required=True, type=int)
    args = parser.parse_args()
    main(args.business_id)
