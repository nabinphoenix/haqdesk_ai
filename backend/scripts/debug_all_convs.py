import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message

def main():
    db = SessionLocal()
    try:
        convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
        print(f"=== Total Conversations in DB: {len(convs)} ===")
        for c in convs:
            cust = db.query(Customer).filter(Customer.id == c.customer_id).first()
            cust_name = cust.display_name if cust else "Unknown Customer"
            msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
            latest_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.id.desc()).first()
            content_snippet = latest_msg.content[:40].encode('ascii', 'backslashreplace').decode('ascii') if (latest_msg and latest_msg.content) else "None"
            print(f"Conv ID: {c.id} | CustID: {c.customer_id} ('{cust_name}') | Platform: {cust.platform if cust else 'N/A'} | Status: {c.status} | IsDeleted: {c.is_deleted}")
            if latest_msg:
                print(f"   Latest Msg: [{latest_msg.sender_type}] '{content_snippet}' (Platform: {latest_msg.platform})")
            print("-" * 60)
    finally:
        db.close()

if __name__ == "__main__":
    main()
