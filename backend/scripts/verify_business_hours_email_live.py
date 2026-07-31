"""Live verification for colon-containing values in an AI email reply."""

import time
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services.email_poller import run_email_poll
from app.services.email_service import send_email
from scripts.verify_email_auto_mode_live import find_database_result, find_reply


def main():
    marker = datetime.now().strftime("%Y%m%d-%H%M%S")
    subject = f"HaqDesk Business Hours Formatting Test {marker}"
    body = (
        "<p>Hello TechSuru,</p>"
        "<p>Please confirm your standard business hours. What time do you "
        "open and close, and which days are you available?</p>"
        f"<p>Test marker: {marker}</p>"
    )
    print(f"TEST_SUBJECT={subject}")
    if not send_email(settings.TECHSURU_IMAP_EMAIL, subject, body):
        raise RuntimeError("Initial SMTP test email was not accepted")

    database_result = None
    reply_result = None
    for attempt in range(1, 7):
        time.sleep(10)
        run_email_poll()
        database_result = find_database_result(subject)
        reply_result = find_reply(subject)
        print(
            f"attempt={attempt} "
            f"database_reply={bool(database_result and database_result['reply_message_id'])} "
            f"imap_reply={bool(reply_result)}"
        )
        if database_result and database_result["reply_message_id"] and reply_result:
            break

    if not reply_result:
        raise RuntimeError("Reply was not found in the real recipient inbox")
    received_html = reply_result["html_body"] or ""
    if "<strong>Our standard business hours are 9:</strong>" in received_html:
        raise RuntimeError("Time value was incorrectly formatted as a label")
    if "9: 00" in received_html:
        raise RuntimeError("Time value contains an inserted space")

    print(f"DATABASE_RESULT={database_result}")
    print(
        "IMAP_REPLY_METADATA="
        f"{dict(reply_result, html_body='<omitted>')}"
    )
    print("RECEIVED_HTML_START")
    print(received_html)
    print("RECEIVED_HTML_END")
    print("LIVE_BUSINESS_HOURS_FORMATTING_VERIFIED=true")


if __name__ == "__main__":
    main()
