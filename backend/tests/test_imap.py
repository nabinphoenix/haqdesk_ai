import imaplib
from app.core.config import settings

def test_imap_connection():
    try:
        mail = imaplib.IMAP4_SSL(settings.TECHSURU_IMAP_HOST, settings.TECHSURU_IMAP_PORT)
        mail.login(settings.TECHSURU_IMAP_EMAIL, settings.TECHSURU_IMAP_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        count = len(messages[0].split()) if messages[0] else 0
        print(f"IMAP connection successful!")
        print(f"Unread emails in inbox: {count}")
        mail.logout()
        return True
    except Exception as e:
        print(f"IMAP connection failed: {e}")
        return False

if __name__ == "__main__":
    test_imap_connection()
