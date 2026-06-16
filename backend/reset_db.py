from sqlalchemy import create_engine, MetaData, Table, text
from app.core.config import settings
from app.core.database import Base
# Import all models
from app.models.user import User
from app.models.business import Business
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.integration import Integration

def reset_haqdesk_tables():
    engine = create_engine(settings.DATABASE_URL)
    metadata = MetaData()
    
    # List of tables we want to ensure are clean
    haqdesk_tables = [
        "messages",
        "conversations",
        "integrations",
        "customers",
        "users",
        "businesses"
    ]
    
    print(f"🔄 Resetting HaqDesk tables in: {settings.DATABASE_URL.split('@')[-1]}")
    
    # Use high-level drop to handle dependencies
    # We drop in reverse order of dependencies
    for table_name in haqdesk_tables:
        try:
            print(f"🗑️  Dropping table {table_name} (if exists)...")
            # We use text-based drop to avoid dependency issues during metadata load
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                conn.commit()
        except Exception as e:
            print(f"⚠️  Could not drop {table_name}: {e}")

    print("🏗️  Recreating HaqDesk tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ HaqDesk tables successfully recreated!")

if __name__ == "__main__":
    confirm = input("⚠️ This will DELETE all data in users, conversations, messages, etc. Continue? (y/n): ")
    if confirm.lower() == 'y':
        reset_haqdesk_tables()
    else:
        print("❌ Reset cancelled.")
