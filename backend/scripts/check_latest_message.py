import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.message import Message

def main():
    db = SessionLocal()
    try:
        messages = db.query(Message).order_by(Message.id.desc()).limit(5).all()
        print(f"--- Top 5 Latest Messages ---")
        for m in messages:
            print(f"ID={m.id} | Sender={m.sender_type} | Content='{m.content}' | Platform={m.platform} | Timestamp={m.timestamp}")
            print(f"   ai_draft='{m.ai_draft}'")
            print(f"   ai_language='{m.ai_language}' | sentiment='{m.sentiment}'")
            print(f"   ai_metadata={m.ai_metadata}")
            print("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    main()
