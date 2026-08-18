import sys
sys.path.insert(0, '.')

# Step 1 - Config check
from app.core.config import settings
print('=== TECHSURU CONFIG ===')
print('EMAIL:', settings.TECHSURU_IMAP_EMAIL)
print('PASSWORD SET:', bool(settings.TECHSURU_IMAP_PASSWORD))
print('HOST:', settings.TECHSURU_IMAP_HOST)
print('PORT:', settings.TECHSURU_IMAP_PORT)

# Step 2 - DB integrations
from app.core.database import SessionLocal
from app.models.integration import Integration
db = SessionLocal()
rows = db.query(Integration).filter(Integration.platform == 'email').all()
print('\n=== EMAIL INTEGRATIONS IN DB ===')
if rows:
    for r in rows:
        m = r.metadata_json or {}
        print('  biz=%s email=%s status=%s' % (r.business_id, m.get('email') or r.page_id, r.status))
else:
    print('  None found')
db.close()

# Step 3 - Poll configs
from app.services.email_poller import build_email_poll_configs
db2 = SessionLocal()
configs = build_email_poll_configs(db2)
db2.close()
print('\n=== POLL CONFIGS ===')
for c in configs:
    print('  biz=%s email=%s host=%s' % (c['business_id'], c['imap_email'], c['imap_host']))
if not configs:
    print('  EMPTY - nothing will be polled!')
