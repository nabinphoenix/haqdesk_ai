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
        customers = db.query(Customer).filter(Customer.display_name.ilike("%Jagadish%")).all()
        print(f"=== Found {len(customers)} Customer records matching 'Jagadish' ===")
        for c in customers:
            print(f"Customer ID: {c.id} | Platform: {c.platform} | PSID/UserID: {c.platform_user_id} | Name: '{c.display_name}' | MergedInto: {c.merged_into_id}")
            convs = db.query(Conversation).filter(Conversation.customer_id == c.id).all()
            for conv in convs:
                msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
                latest_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).first()
                print(f"   -> Conversation ID: {conv.id} | Status: {conv.status} | IsDeleted: {conv.is_deleted} | CreatedAt: {conv.created_at} | MsgCount: {msg_count}")
                if latest_msg:
                    print(f"      Latest Msg ID {latest_msg.id}: '{latest_msg.content[:60]}' (sender: {latest_msg.sender_type}, platform: {latest_msg.platform})")
        
        print("\n=== Checking all duplicate Customers across DB ===")
        all_customers = db.query(Customer).all()
        by_name = {}
        for c in all_customers:
            name = c.display_name.strip().lower() if c.display_name else "unknown"
            by_name.setdefault(name, []).append(c)
        
        duplicates = {k: v for k, v in by_name.items() if len(v) > 1}
        print(f"Found {len(duplicates)} duplicate customer names in DB:")
        for name, cust_list in duplicates.items():
            print(f" - Name: '{name}' ({len(cust_list)} records):")
            for c in cust_list:
                print(f"     ID={c.id}, Platform={c.platform}, PSID={c.platform_user_id}, Merged={c.merged_into_id}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
