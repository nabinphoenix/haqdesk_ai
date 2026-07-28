import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.core.database import SessionLocal
from sqlalchemy import text


def migrate_remove_pgvector():
    """Migration: Drop `embedding` vector column from `knowledge_chunks` table."""
    db = SessionLocal()
    try:
        print("[Migration] Dropping `embedding` column from `knowledge_chunks` table...")
        db.execute(text("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding;"))
        db.commit()
        print("✅ Column `embedding` dropped successfully from PostgreSQL `knowledge_chunks`.")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_remove_pgvector()
