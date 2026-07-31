import asyncio
import logging
import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.webhook_service import process_incoming_message_in_background
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.business import Business

logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing process_incoming_message_in_background...")
    db = SessionLocal()
    try:
        # Get or create test business
        biz = db.query(Business).first()
        if not biz:
            print("No business found in database!")
            return
        
        # Get or create test customer & conversation
        cust = db.query(Customer).filter(Customer.business_id == biz.id).first()
        if not cust:
            print("No customer found in DB")
            return
            
        conv = db.query(Conversation).filter(Conversation.customer_id == cust.id).first()
        if not conv:
            print("No conversation found in DB")
            return

        # Insert a dummy customer message
        msg = Message(
            conversation_id=conv.id,
            sender_type="customer",
            content="Kasto xa tapai ko shop ma laptop ko price?",
            platform="messenger"
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        print(f"Running pipeline for Message ID {msg.id}, Conv ID {conv.id}, Business ID {biz.id}...")
        await process_incoming_message_in_background(
            message_id=msg.id,
            conversation_id=conv.id,
            message_text=msg.content,
            business_id=biz.id
        )

        db.refresh(msg)
        print("Updated Message ai_draft:", msg.ai_draft)

    except Exception as e:
        print("EXPLICIT ERROR CAUGHT IN TEST SCRIPT:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
