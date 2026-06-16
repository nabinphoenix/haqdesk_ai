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
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    print("Running Database Migration for RAG Chatbot Integration...")
    
    with engine.begin() as conn:
        try:
            print("Enabling pgvector extension in PostgreSQL...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("pgvector extension enabled successfully.")
        except Exception as e:
            print(f"Error enabling pgvector extension (might require superuser privileges): {e}")
            print("Continuing migration, assuming extension is already enabled or handled...")

    # Create the new knowledge_documents and knowledge_chunks tables (and any others missing)
    print("Creating new tables (knowledge_documents, knowledge_chunks)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise e

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
