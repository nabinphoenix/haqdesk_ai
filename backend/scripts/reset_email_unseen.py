"""
Run this once to mark all inbox emails as UNSEEN (unread) in Gmail via IMAP,
so the HaqDesk poller can re-pick them up.
"""
import imaplib
import sys

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
EMAIL = "techsuru1@gmail.com"
PASSWORD = "gqus yoeq kyii pgrq"   # App password from .env

print(f"Connecting to {IMAP_HOST}:{IMAP_PORT} as {EMAIL}...")
try:
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL, PASSWORD)
    print("Login: SUCCESS")

    mail.select("inbox")

    # Find ALL emails in inbox (not just unread)
    status, messages = mail.search(None, "ALL")
    all_ids = messages[0].split() if messages[0] else []
    print(f"Total emails in inbox: {len(all_ids)}")

    # Find only SEEN (read) ones
    status2, seen_msgs = mail.search(None, "SEEN")
    seen_ids = seen_msgs[0].split() if seen_msgs[0] else []
    print(f"Currently READ emails: {len(seen_ids)}")

    if not seen_ids:
        print("No read emails to mark as unread. Nothing to do.")
    else:
        # Ask before mass-unmarking
        print(f"\nWill mark {len(seen_ids)} emails as UNREAD.")
        for eid in seen_ids:
            mail.store(eid, "-FLAGS", "\\Seen")
        print(f"Done! Marked {len(seen_ids)} emails as UNREAD (UNSEEN).")
        print("The HaqDesk poller will now pick these up on the next 30-second cycle.")

    mail.logout()

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
