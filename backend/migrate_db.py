import psycopg2
from urllib.parse import urlparse, unquote
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base

# Import all models to ensure Base.metadata is populated
from app.models.user import User
from app.models.business import Business
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.integration import Integration
from app.models.customer_identity import CustomerIdentity
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.models.invitation import Invitation


def _enable_vector_extension():
    """
    Enable pgvector using a raw psycopg2 connection with autocommit=True.
    CREATE EXTENSION cannot run inside a transaction block, so we can't use
    SQLAlchemy's normal connection here.
    """
    db_url = settings.DATABASE_URL  # e.g. postgresql://user:pass@host:port/dbname
    parsed = urlparse(db_url)

    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=unquote(parsed.password or ""),
    )
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Enabling pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("[OK] pgvector extension is ready.")
    finally:
        cur.close()
        conn.close()


def migrate():
    # Step 1: Enable the vector extension FIRST (must be autocommit)
    _enable_vector_extension()

    engine = create_engine(settings.DATABASE_URL)

    print("Running Database Migration...")

    with engine.connect() as conn:
        # Add new columns to customers table safely
        columns_to_add = [
            ("avatar_url", "VARCHAR"),
            ("notes", "TEXT"),
            ("is_merged", "BOOLEAN DEFAULT FALSE"),
            ("merged_into_id", "INTEGER"),
            ("potential_match_customer_id", "INTEGER"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                print(f"Adding column {col_name} to customers...")
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"  [OK] Column '{col_name}' added.")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  [SKIP] Column '{col_name}' already exists. Skipping.")
                else:
                    print(f"  [ERROR] Error adding '{col_name}': {e}")

        # Add new columns to messages table safely
        messages_columns_to_add = [
            ("ai_draft", "TEXT"),
            ("ai_language", "VARCHAR"),
            ("sentiment", "VARCHAR"),
            ("ai_metadata", "JSON"),
        ]

        for col_name, col_type in messages_columns_to_add:
            try:
                print(f"Adding column {col_name} to messages...")
                conn.execute(text(f"ALTER TABLE messages ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"  [OK] Column '{col_name}' added.")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  [SKIP] Column '{col_name}' already exists. Skipping.")
                else:
                    print(f"  [ERROR] Error adding '{col_name}': {e}")

        # ---- integrations table ----
        integration_columns = [
            ("page_id", "VARCHAR"),
            ("page_name", "VARCHAR"),
        ]
        for col_name, col_type in integration_columns:
            try:
                print(f"Adding column {col_name} to integrations...")
                conn.execute(text(f"ALTER TABLE integrations ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Column '{col_name}' added.")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Column '{col_name}' already exists. Skipping.")
                else:
                    print(f"  [ERROR] Error adding '{col_name}': {e}")

        # ---- businesses table ----
        business_columns = [
            ("email", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("description", "TEXT"),
            ("logo_url", "VARCHAR"),
            ("website", "VARCHAR"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
        ]
        for col_name, col_type in business_columns:
            try:
                print(f"Adding column {col_name} to businesses...")
                conn.execute(text(f"ALTER TABLE businesses ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Column '{col_name}' added.")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Column '{col_name}' already exists. Skipping.")
                else:
                    print(f"  [ERROR] Error adding '{col_name}': {e}")

    # Step 2: Create all new tables (knowledge_documents, knowledge_chunks, etc.)
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create indexes safely
    with engine.connect() as conn:
        indexes = [
            """CREATE INDEX IF NOT EXISTS ix_messages_conversation_timestamp 
               ON messages (conversation_id, timestamp)""",
            
            """CREATE INDEX IF NOT EXISTS ix_conversations_business_created 
               ON conversations (business_id, created_at DESC)""",
            
            """CREATE INDEX IF NOT EXISTS ix_customers_business_platform 
               ON customers (business_id, platform, platform_user_id)""",
            
            """CREATE INDEX IF NOT EXISTS ix_knowledge_documents_business 
               ON knowledge_documents (business_id)""",
            
            """CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_business_document 
               ON knowledge_chunks (business_id, document_id)""",
        ]
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
                print("Index created.")
            except Exception as e:
                conn.rollback()
                print(f"Index skipped: {e}")

    print("[SUCCESS] Migration completed successfully!")


if __name__ == "__main__":
    migrate()
