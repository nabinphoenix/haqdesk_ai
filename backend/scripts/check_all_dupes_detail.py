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
        print("=== ALL CUSTOMERS IN DB ===")
        customers = db.query(Customer).all()
        for c in customers:
            conv_count = db.query(Conversation).filter(Conversation.customer_id == c.id).count()
            print(f"Customer ID: {c.id} | DisplayName: '{c.display_name}' | Platform: {c.platform} | PSID: '{c.platform_user_id}' | MergedInto: {c.merged_into_id} | Convs: {conv_count}")
        
        print("\n=== ALL CONVERSATIONS IN DB ===")
        convs = db.query(Conversation).order_by(Conversation.id.asc()).all()
        for conv in convs:
            cust = db.query(Customer).filter(Customer.id == conv.customer_id).first()
            msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            latest = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).first()
            content = repr(latest.content[:30]) if latest else "None"
            print(f"Conv ID: {conv.id} | CustID: {conv.customer_id} ('{cust.display_name if cust else 'Unknown'}', Platform: {cust.platform if cust else 'N/A'}) | Status: {conv.status} | Msgs: {msg_count} | Latest: {content}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
