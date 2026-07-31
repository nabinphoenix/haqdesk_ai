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
        for cid in [2, 13]:
            conv = db.query(Conversation).filter(Conversation.id == cid).first()
            if not conv:
                continue
            cust = db.query(Customer).filter(Customer.id == conv.customer_id).first()
            print(f"=== CONVERSATION {cid} ===")
            print(f"Customer Record: ID={cust.id}, Name='{cust.display_name}', Platform={cust.platform}, PSID='{cust.platform_user_id}', MergedInto={cust.merged_into_id}, MatchID={cust.potential_match_customer_id}")
            msgs = db.query(Message).filter(Message.conversation_id == cid).order_by(Message.id.asc()).all()
            print(f"Messages count: {len(msgs)}")
            for m in msgs:
                print(f"  Msg #{m.id} | [{m.sender_type}] '{m.content[:70]}' (Platform: {m.platform})")
            print("\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
