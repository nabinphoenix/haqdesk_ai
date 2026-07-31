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
        print("=== REASSIGNING MERGED CONVERSATIONS IN DATABASE ===")
        
        # 1. Jagadish Kharel (Customer 2 merged into Customer 3)
        cust2 = db.query(Customer).filter(Customer.id == 2).first()
        cust3 = db.query(Customer).filter(Customer.id == 3).first()
        
        if cust2 and cust3:
            print(f"Syncing Customer 3 ('{cust3.display_name}') with primary platform '{cust2.platform}' (PSID {cust2.platform_user_id})")
            cust3.platform = cust2.platform
            cust3.platform_user_id = cust2.platform_user_id
            
            convs2 = db.query(Conversation).filter(Conversation.customer_id == 2).all()
            print(f"Reassigning {len(convs2)} conversations from Customer 2 to Customer 3...")
            for conv in convs2:
                conv.customer_id = 3
                print(f" -> Reassigned Conv {conv.id} to Customer 3")

        # 2. junior_jk_berlin (Customer 4 merged into Customer 5)
        cust4 = db.query(Customer).filter(Customer.id == 4).first()
        cust5 = db.query(Customer).filter(Customer.id == 5).first()
        
        if cust4 and cust5:
            print(f"Syncing Customer 5 ('{cust5.display_name}') with primary platform '{cust4.platform}' (PSID {cust4.platform_user_id})")
            cust5.platform = cust4.platform
            cust5.platform_user_id = cust4.platform_user_id
            
            convs4 = db.query(Conversation).filter(Conversation.customer_id == 4).all()
            print(f"Reassigning {len(convs4)} conversations from Customer 4 to Customer 5...")
            for conv in convs4:
                conv.customer_id = 5
                print(f" -> Reassigned Conv {conv.id} to Customer 5")

        db.commit()
        print("✅ Database reassignment completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
