import asyncio
import logging
import threading
import httpx

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.integration import Integration
from app.models.message import Message
from app.services.rag_service import rag_service
from app.services.sentiment_service import detect_sentiment

logger = logging.getLogger("uvicorn")


async def process_incoming_message_in_background(message_id: int, conversation_id: int, message_text: str, business_id: int):
    """
    Analyzes the message for language and sentiment (BERT),
    queries the RAG knowledge base, generates an AI draft reply,
    and updates the Message in the database.
    Also creates a separate 'ai' sender_type message to trigger the frontend float box.
    """
    db = SessionLocal()
    try:
        # 1. Detect language
        language = rag_service.detect_language(message_text)
        
        # 2. Detect sentiment
        sentiment = detect_sentiment(message_text)
        
        # 3. Query RAG to get the suggested draft reply (which also translates/matches the language style)
        rag_result = await rag_service.query(
            question=message_text,
            business_id=business_id,
            db=db,
            language=language,
            sentiment=sentiment
        )
        
        draft = None
        metadata = None
        if rag_result and rag_result.get("answer"):
            draft = rag_result["answer"]
            metadata = rag_result.get("metadata")

        # 4. Update the original customer message in the database with the metadata
        msg = db.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.ai_draft = draft
            msg.ai_language = language
            msg.sentiment = sentiment
            if hasattr(msg, "ai_metadata"):
                msg.ai_metadata = metadata
            db.commit()
            logger.info(f"Updated customer message {message_id} with sentiment={sentiment}, language={language}, has_draft={draft is not None}")

        # 5. If draft exists, also create a sender_type=\"ai\" message so the frontend's floating AISuggestionBox can fetch it
        if draft:
            # First clean up any old unread/unacted AI messages in this conversation to avoid duplicates
            db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.sender_type == "ai"
            ).delete()
            db.commit()

            ai_msg = Message(
                conversation_id=conversation_id,
                sender_type="ai",
                content=draft,
                platform=msg.platform if msg else "messenger"
            )
            db.add(ai_msg)
            db.commit()
            logger.info(f"Saved AI suggested message for conversation {conversation_id}")
            
    except Exception as e:
        logger.error(f"Error in process_incoming_message_in_background: {e}")
    finally:
        db.close()

class WebhookService:
    async def process_facebook_webhook(self, db: Session, data: dict, background_tasks: BackgroundTasks = None):
        """
        Process incoming Facebook Messenger webhook data
        """
        if data.get("object") != "page":
            return
        
        for entry in data.get("entry", []):
            # Check for regular messaging events safely
            await self._process_messaging_events(db, entry.get("messaging") or [], "facebook", background_tasks)
            # Check for standby events (when app is not primary receiver) safely
            await self._process_messaging_events(db, entry.get("standby") or [], "facebook", background_tasks)

    async def process_instagram_webhook(self, db: Session, data: dict, background_tasks: BackgroundTasks = None):
        """
        Process incoming Instagram Direct webhook data
        """
        if data.get("object") != "instagram":
            return
        
        for entry in data.get("entry", []):
            # Check for regular messaging events safely
            await self._process_messaging_events(db, entry.get("messaging") or [], "instagram", background_tasks)
            # Check for standby events safely
            await self._process_messaging_events(db, entry.get("standby") or [], "instagram", background_tasks)

    async def _process_messaging_events(self, db: Session, events: list, platform: str, background_tasks: BackgroundTasks = None):
        """Helper to process a list of messaging events"""
        if not events:
            return
            
        for event in events:
            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                continue
                
            recipient_id = event.get("recipient", {}).get("id")

            # 1. Handle actual text messages
            if "message" in event:
                # Ignore echo messages (messages sent by the page itself)
                if event["message"].get("is_echo"):
                    logger.info(f"🤫 {platform.capitalize()} Ignoring echo message (sent by page)")
                    continue
                    
                message_text = event["message"].get("text", "")
                # Handle attachments (images, etc) if text is empty
                if not message_text and event["message"].get("attachments"):
                    message_text = "[Attachment]"
                
                if message_text:
                    await self._handle_platform_message(
                        db, 
                        platform=platform,
                        sender_id=sender_id,
                        message_text=message_text,
                        background_tasks=background_tasks,
                        recipient_id=recipient_id
                    )
            
            # 2. Handle Delivery Receipts (log them so we know they arrived)
            elif "delivery" in event:
                watermark = event["delivery"].get("watermark")
                logger.info(f"🚚 {platform.capitalize()} Delivery Receipt from {sender_id} (Watermark: {watermark}) - Ignoring.")
                
            # 3. Handle Read Receipts
            elif "read" in event:
                watermark = event["read"].get("watermark")
                logger.info(f"👁️ {platform.capitalize()} Read Receipt from {sender_id} (Watermark: {watermark}) - Ignoring.")
            
            # 4. Handle Postbacks (Buttons, Get Started)
            elif "postback" in event:
                title = event["postback"].get("title")
                await self._handle_platform_message(
                    db,
                    platform=platform,
                    sender_id=sender_id,
                    message_text=f"[Postback: {title}]",
                    background_tasks=background_tasks,
                    recipient_id=recipient_id
                )

    async def process_whatsapp_webhook(self, db: Session, data: dict, background_tasks: BackgroundTasks = None):
        """
        Process incoming WhatsApp Cloud API webhook data
        """
        if data.get("object") != "whatsapp_business_account":
            return
        
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        sender_id = message["from"]
                        message_text = ""
                        if message.get("type") == "text":
                            message_text = message["text"].get("body", "")
                        
                        # Get sender name if available
                        display_name = None
                        contacts = value.get("contacts", [])
                        if contacts:
                            display_name = contacts[0].get("profile", {}).get("name")

                        await self._handle_platform_message(
                            db, 
                            platform="whatsapp",
                            sender_id=sender_id,
                            message_text=message_text,
                            display_name=display_name,
                            background_tasks=background_tasks
                        )

    async def _handle_platform_message(
        self, db: Session, platform: str, sender_id: str,
        message_text: str, display_name: str = None,
        background_tasks: BackgroundTasks = None,
        recipient_id: str = None
    ):
        """Internal helper to save messages for any platform"""
        logger.info(f"Processing {platform} message from {sender_id}: {message_text}")
        
        # 1. Find business by matching recipient_id (page_id) to integrations table
        business = None
        if recipient_id:
            integration = db.query(Integration).filter(
                Integration.page_id == recipient_id,
                Integration.platform == platform,
                Integration.status == "active"
            ).first()
            if integration:
                business = db.query(Business).filter(
                    Business.id == integration.business_id
                ).first()

        # 2. Prevent fallback to first business (Security Fix)
        if not business:
            logger.error(f"No integration/business found for page_id={recipient_id}. Cannot process message.")
            return
        
        # 3. Find or Create Customer
        customer = db.query(Customer).filter(
            Customer.business_id == business.id,
            Customer.platform_user_id == sender_id,
            Customer.platform == platform
        ).first()
        
        if not customer:
            if not display_name:
                display_name = f"{platform.capitalize()} User {sender_id[:5]}"
                
                # Fetch real name from Meta if possible (Facebook/Instagram)
                if platform in ["facebook", "instagram"]:
                    try:
                        # Note: This might need Page Access Token depending on the platform
                        profile_url = f"https://graph.facebook.com/v18.0/{sender_id}"
                        params = {
                            "fields": "first_name,last_name,name,profile_pic",
                            "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN
                        }
                        async with httpx.AsyncClient() as client: # Use AsyncClient
                            res = await client.get(profile_url, params=params)
                            if res.status_code == 200:
                                profile_data = res.json()
                                if "first_name" in profile_data:
                                    display_name = f"{profile_data.get('first_name')} {profile_data.get('last_name')}"
                                elif "name" in profile_data:
                                    display_name = profile_data.get("name")
                    except Exception as e:
                        logger.error(f"Failed to fetch {platform} profile: {e}")

            # Auto-suggest matching (case-insensitive exact match)
            potential_match_id = None
            if display_name:
                potential_match = db.query(Customer).filter(
                    Customer.display_name.ilike(display_name),
                    Customer.business_id == business.id
                ).first()
                if potential_match:
                    potential_match_id = potential_match.id

            customer = Customer(
                business_id=business.id,
                platform=platform,
                platform_user_id=sender_id,
                display_name=display_name,
                potential_match_customer_id=potential_match_id
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        # 3. Find or Create Conversation
        conversation = db.query(Conversation).filter(
            Conversation.customer_id == customer.id,
            Conversation.status == "open"
        ).first()
        
        if not conversation:
            conversation = Conversation(
                business_id=business.id,
                customer_id=customer.id,
                status="open"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 4. Save the Customer Message
        new_message = Message(
            conversation_id=conversation.id,
            sender_type="customer",
            content=message_text,
            platform=platform
        )
        db.add(new_message)
        db.commit()
        
        # Trigger background processing (sentiment, language, RAG draft)
        if background_tasks:
            background_tasks.add_task(
                process_incoming_message_in_background,
                new_message.id, conversation.id, new_message.content, business.id
            )
        else:
            # Fallback to threading with new event loop
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(process_incoming_message_in_background(
                    new_message.id, conversation.id, new_message.content, business.id
                ))
                loop.close()
            threading.Thread(target=run_async, daemon=True).start()
        
        logger.info(f"✅ {platform} message successfully saved to database!")


# generate_and_save_draft was removed and unified into process_incoming_message_in_background
