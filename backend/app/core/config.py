from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "HaqDesk AI"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Meta OAuth (Facebook, Instagram, WhatsApp)
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    META_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX: bool = False
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"


    OAUTH_REDIRECT_URI: str = "http://localhost:3000/oauth/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    # AI Centralized Settings
    LLM_PRIMARY_MODEL: str = "groq/qwen/qwen3.6-27b"
    LLM_FALLBACK_MODELS: str = "gemini/gemini-2.0-flash,groq/openai/gpt-oss-120b"
    LLM_TIMEOUT_SECONDS: int = 45
    LLM_MAX_RETRIES_PER_MODEL: int = 1
    LLM_FALLBACK_ENABLED: bool = True

    # Embedding Model
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBEDDING_DIM: int = 1024

    # Ollama (local LLM server for models like gemma3:1b)
    OLLAMA_API_BASE: str = "http://localhost:11434"

    # Provider Keys
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None

    VECTOR_DB_PATH: str = "./vector_db"
    KNOWLEDGE_UPLOAD_ROOT: str = "uploads/knowledge"

    # Qdrant Vector Database
    KNOWLEDGE_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    KNOWLEDGE_MAX_DOCUMENTS: int = 100
    KNOWLEDGE_MAX_STORAGE_BYTES: int = 1024 * 1024 * 1024
    KNOWLEDGE_MAX_EXTRACTED_CHARACTERS: int = 5_000_000
    KNOWLEDGE_INGESTION_MAX_ATTEMPTS: int = 3
    KNOWLEDGE_INGESTION_WORKER_ENABLED: bool = True
    KNOWLEDGE_INGESTION_POLL_SECONDS: float = 2.0
    KNOWLEDGE_INGESTION_STALE_SECONDS: int = 900
    # Set false in production so an unavailable shared Qdrant fails clearly.
    QDRANT_ALLOW_LOCAL_FALLBACK: bool = False
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_PREFIX: str = "haqdesk_business"

    # Email (Gmail SMTP)
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_IMAP_HOST: str = "imap.gmail.com"
    MAIL_IMAP_PORT: int = 993

    # TechSuru fallback email inbox (business_id=1)
    # These must be declared here so pydantic-settings loads them from .env.
    # Without declaration, extra='ignore' silently drops them and the poller
    # never polls techsuru1@gmail.com.
    TECHSURU_IMAP_EMAIL: Optional[str] = None
    TECHSURU_IMAP_PASSWORD: Optional[str] = None
    TECHSURU_IMAP_HOST: str = "imap.gmail.com"
    TECHSURU_IMAP_PORT: int = 993

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
