import os
import logging
from typing import Dict, Any
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger("uvicorn")

def check_database() -> bool:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Preflight: Database connection failed: {e}")
        return False
    finally:
        db.close()

def check_pgvector() -> bool:
    db = SessionLocal()
    try:
        db.execute(text("SELECT '[0]'::vector"))
        return True
    except Exception as e:
        logger.error(f"Preflight: pgvector is not available: {e}")
        return False
    finally:
        db.close()

def check_llm_setup() -> Dict[str, Any]:
    primary_model = settings.LLM_PRIMARY_MODEL
    primary_provider = primary_model.split("/")[0] if "/" in primary_model else ""
    primary_key_name = f"{primary_provider.upper()}_API_KEY" if primary_provider else ""
    
    primary_key_set = False
    if primary_key_name:
        primary_key_set = bool(os.environ.get(primary_key_name) or getattr(settings, primary_key_name, None))
        
    fallback_models = []
    if settings.LLM_FALLBACK_ENABLED and settings.LLM_FALLBACK_MODELS:
        fallbacks = [m.strip() for m in settings.LLM_FALLBACK_MODELS.split(",") if m.strip()]
        for fb in fallbacks:
            fb_provider = fb.split("/")[0] if "/" in fb else ""
            fb_key_name = f"{fb_provider.upper()}_API_KEY" if fb_provider else ""
            fb_key_set = False
            if fb_key_name:
                fb_key_set = bool(os.environ.get(fb_key_name) or getattr(settings, fb_key_name, None))
            fallback_models.append({
                "model": fb,
                "key_set": fb_key_set
            })
            
    return {
        "primary_model": primary_model,
        "primary_key_set": primary_key_set,
        "fallback_models": fallback_models
    }

def check_embedding_model() -> bool:
    try:
        import app.services.rag_service  # noqa: F401 - checks module can be loaded
        return True
    except Exception as e:
        logger.error(f"Preflight: Embedding model setup error: {e}")
        return False

def check_sentiment_model() -> bool:
    try:
        import app.services.sentiment_service  # noqa: F401 - checks module can be loaded
        return True
    except Exception as e:
        logger.error(f"Preflight: Sentiment model setup error: {e}")
        return False

def run_preflight() -> Dict[str, Any]:
    db_ok = check_database()
    pgvector_ok = check_pgvector() if db_ok else False
    llm_info = check_llm_setup()
    embedding_ok = check_embedding_model()
    sentiment_ok = check_sentiment_model()
    
    # Meta credentials check
    meta_credentials = {
        "facebook_client_id_set": bool(settings.FACEBOOK_CLIENT_ID),
        "facebook_client_secret_set": bool(settings.FACEBOOK_CLIENT_SECRET),
        "facebook_page_access_token_set": bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN),
        "facebook_page_id_set": bool(settings.FACEBOOK_PAGE_ID),
        "verify_token_set": bool(settings.META_VERIFY_TOKEN)
    }
    
    ok = db_ok and pgvector_ok and llm_info["primary_key_set"] and embedding_ok and sentiment_ok
    
    return {
        "ok": ok,
        "database": db_ok,
        "pgvector": pgvector_ok,
        "llm": llm_info,
        "embedding_model": embedding_ok,
        "sentiment_model": sentiment_ok,
        "meta_credentials": meta_credentials
    }

if __name__ == "__main__":
    import sys
    print("Running HaqDesk AI Preflight Checks...")
    res = run_preflight()
    print("Preflight Results:")
    print(res)
    if not res["ok"]:
        sys.exit(1)
    sys.exit(0)
