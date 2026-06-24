from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routers import auth, integrations, inbox, customers, knowledge, whatsapp, team

app = FastAPI(title="HaqDesk AI API")

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

@app.get("/")
async def root():
    return {"message": "Welcome to HaqDesk AI API"}

@app.get("/health/preflight")
async def health_preflight():
    from app.core.preflight import run_preflight
    return run_preflight()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
