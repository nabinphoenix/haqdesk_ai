from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routers import auth, integrations, inbox, customers, knowledge, whatsapp, team, analytics, super_admin, internal_messages, settings as settings_router

import threading
import time
from app.services.email_poller import run_email_poll
from app.services.knowledge_ingestion import start_knowledge_ingestion_worker

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.database import engine
import os

app = FastAPI(title="HaqDesk AI API")

# Ensure uploads directory exists and mount it
os.makedirs("uploads/attachments", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/audio", StaticFiles(directory="uploads/attachments"), name="audio")

def start_email_polling():
    """Run email polling in a background thread every 30 seconds."""
    def poll_loop():
        # Wait 10 seconds after startup before first poll
        time.sleep(10)
        while True:
            try:
                run_email_poll()
            except Exception as e:
                print(f"[EMAIL POLL] Error in poll loop: {e}")
            time.sleep(30)

    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()
    print("[EMAIL POLL] Background email polling started")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Keep the configured frontend URL for deployed environments.  During local
    # development Next.js may select another port when 3000 is already in use,
    # so allow localhost/127.0.0.1 on any port as well.
    allow_origins=[settings.FRONTEND_URL.rstrip("/")],
    allow_origin_regex=r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for OAuth state storage
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(inbox.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1/team")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(super_admin.router, prefix="/api/v1")
app.include_router(internal_messages.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to HaqDesk AI API"}

@app.get("/health/preflight")
async def health_preflight():
    from app.core.preflight import run_preflight
    return run_preflight()

@app.on_event("startup")
async def startup_event():
    # A fresh RDS database has no tables. Populate the complete SQLAlchemy
    # metadata before applying additive compatibility migrations below.
    # Importing every model is intentional: Base only knows about models that
    # have been imported into this process.
    import app.models  # noqa: F401
    from app.models.internal_messaging import InternalThread, InternalThreadParticipant, InternalMessage
    from app.models.faq_opportunity import FAQOpportunityFeedback
    from app.models.knowledge import KnowledgeIngestionJob, AgentReplyFeedback
    from app.core.database import Base

    Base.metadata.create_all(bind=engine)

    # Keep existing databases compatible without requiring a full migration
    # framework. Presence uses this timestamp to expire stale users.
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE"
        ))
        connection.execute(text(
            "ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS storage_path VARCHAR"
        ))
        for column_sql in (
            'source_type VARCHAR',
            'file_size INTEGER DEFAULT 0',
            'checksum VARCHAR(64)',
            'processing_error TEXT',
            'processing_started_at TIMESTAMP',
            'processed_at TIMESTAMP',
            'ingestion_attempts INTEGER DEFAULT 0',
        ):
            connection.execute(text(
                f'ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS {column_sql}'
            ))
        connection.execute(text("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN"))
        connection.execute(text("UPDATE knowledge_documents SET source_type = 'upload' WHERE source_type IS NULL"))
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE agent_reply_feedback ADD COLUMN IF NOT EXISTS knowledge_document_id INTEGER"))
    # Re-queue legacy processing documents so failed uploads are recoverable.
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO knowledge_ingestion_jobs (document_id, business_id, status, attempts, available_at, created_at) SELECT d.id, d.business_id, 'pending', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM knowledge_documents d WHERE d.status = 'processing' AND d.storage_path IS NOT NULL AND NOT EXISTS (SELECT 1 FROM knowledge_ingestion_jobs j WHERE j.document_id = d.id)"))
        connection.execute(text("UPDATE knowledge_documents SET status = 'failed', processing_error = 'No stored file is available for ingestion.' WHERE status = 'processing' AND storage_path IS NULL"))
    start_knowledge_ingestion_worker()
    start_email_polling()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
