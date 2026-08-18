"""
Direct email poll test — runs one poll cycle with full verbose logging.
Run from backend/ directory: python scripts/test_poll_now.py
"""
import sys
import logging
sys.path.insert(0, '.')

# Enable full logging to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("STEP 1: Loading settings...")
from app.core.config import settings
print(f"  TECHSURU_IMAP_EMAIL    = {settings.TECHSURU_IMAP_EMAIL}")
print(f"  TECHSURU_IMAP_PASSWORD = {'SET (' + settings.TECHSURU_IMAP_PASSWORD[:4] + '...)' if settings.TECHSURU_IMAP_PASSWORD else 'NOT SET !!!'}")
print(f"  TECHSURU_IMAP_HOST     = {settings.TECHSURU_IMAP_HOST}")
print(f"  TECHSURU_IMAP_PORT     = {settings.TECHSURU_IMAP_PORT}")

print()
print("=" * 60)
print("STEP 2: Checking DB email integrations...")
from app.core.database import SessionLocal
from app.models.integration import Integration
db = SessionLocal()
rows = db.query(Integration).filter(Integration.platform == 'email').all()
if rows:
    for r in rows:
        m = r.metadata_json or {}
        print(f"  DB Integration: business_id={r.business_id}, email={m.get('email') or r.page_id}, status={r.status}")
else:
    print("  No email integrations in DB — will use TECHSURU fallback")
db.close()

print()
print("=" * 60)
print("STEP 3: Building poll configs...")
from app.services.email_poller import build_email_poll_configs
db2 = SessionLocal()
try:
    configs = build_email_poll_configs(db2)
finally:
    db2.close()

if not configs:
    print("  ERROR: No poll configs built! Poller has nothing to poll.")
    print("  Check if TECHSURU_IMAP_EMAIL is loaded correctly.")
    sys.exit(1)

for c in configs:
    print(f"  Config: business_id={c['business_id']}, imap_email={c['imap_email']}, host={c['imap_host']}:{c['imap_port']}")

print()
print("=" * 60)
print("STEP 4: Testing IMAP connection directly...")
import imaplib

for c in configs:
    print(f"  Connecting to {c['imap_host']}:{c['imap_port']} as {c['imap_email']}...")
    try:
        mail = imaplib.IMAP4_SSL(c['imap_host'], c['imap_port'])
        mail.login(c['imap_email'], c['imap_password'])
        mail.select('inbox')
        status, messages = mail.search(None, 'UNSEEN')
        unseen_ids = messages[0].split() if messages[0] else []
        print(f"  LOGIN OK — {len(unseen_ids)} UNSEEN emails found")
        if unseen_ids:
            print(f"  First few IDs: {[x.decode() for x in unseen_ids[:5]]}")
        mail.logout()
    except Exception as e:
        print(f"  IMAP ERROR: {e}")

print()
print("=" * 60)
print("STEP 5: Running one full poll cycle...")
from app.services.email_poller import poll_emails_for_business
for c in configs:
    print(f"  Polling business_id={c['business_id']} ({c['imap_email']})...")
    poll_emails_for_business(
        business_id=c['business_id'],
        imap_email=c['imap_email'],
        imap_password=c['imap_password'],
        imap_host=c['imap_host'],
        imap_port=c['imap_port'],
    )
    print(f"  Poll complete for business_id={c['business_id']}")

print()
print("Done! Check your HaqDesk inbox now.")
