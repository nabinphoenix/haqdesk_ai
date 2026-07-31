from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routers import auth, integrations, inbox, customers, knowledge, whatsapp, team, analytics, super_admin, settings as settings_router

import threading
import time
from app.services.email_poller import run_email_poll

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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

@app.get("/")
async def root():
    return {"message": "Welcome to HaqDesk AI API"}

@app.get("/health/preflight")
async def health_preflight():
    from app.core.preflight import run_preflight
    return run_preflight()

@app.on_event("startup")
async def startup_event():
    start_email_polling()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
