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


from datetime import datetime, timezone

async def process_incoming_message_in_background(message_id: int, conversation_id: int, message_text: str, business_id: int):
    """
    Analyzes the message for language and sentiment (BERT),
    queries the RAG knowledge base, generates an AI draft reply,
    and updates the Message in the database.
    If business.ai_response_mode is 'auto', automatically sends the AI reply to the customer.
    If 'review', saves the AI suggested draft for human review.
    """
    db = SessionLocal()
    try:
        # 1. Detect language
        language = rag_service.detect_language(message_text)
        
        # 2. Detect sentiment
        sentiment = detect_sentiment(message_text)
        
        # 3. Fetch business AI response mode (auto vs review)
        business = db.query(Business).filter(Business.id == business_id).first()
        mode = (business.ai_response_mode if business and business.ai_response_mode else "review").lower()

        # 4. Query RAG with conversation memory history context and business mode
        rag_result = await rag_service.query(
            question=message_text,
            business_id=business_id,
            conversation_id=conversation_id,
            current_message_id=message_id,
            mode=mode,
            db=db,
            language=language,
            sentiment=sentiment
        )
        
        draft = None
        metadata = None
        if rag_result and rag_result.get("answer"):
            draft = rag_result["answer"]
            metadata = rag_result.get("metadata")

        # 5. Update the original customer message in the database with the metadata
        msg = db.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.ai_draft = draft
            msg.ai_language = language
            msg.sentiment = sentiment
            if hasattr(msg, "ai_metadata"):
                msg.ai_metadata = metadata
            db.commit()
            logger.info(f"Updated customer message {message_id} with sentiment={sentiment}, language={language}, has_draft={draft is not None}")

        if draft:
            if mode == "auto":
                # AUTO MODE: Instantly send response back to customer on platform
                logger.info(f"🤖 [AUTO MODE] Sending AI response automatically for conversation {conversation_id}")
                # Clear ai_draft on customer message in Auto Mode so UI renders only the auto-sent message bubble
                if msg:
                    msg.ai_draft = None
                    db.commit()
                await dispatch_auto_ai_reply(db, conversation_id, business_id, draft)
            else:
                # REVIEW MODE: Create a sender_type="ai" pending message for human review
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
                logger.info(f"Saved AI suggested message for conversation {conversation_id} (Review Mode)")
            
    except Exception as e:
        logger.error(f"Error in process_incoming_message_in_background: {e}")
    finally:
        db.close()


async def dispatch_auto_ai_reply(db: Session, conversation_id: int, business_id: int, reply_text: str):
    """Internal helper to dispatch AI reply automatically when in auto mode."""
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return
        customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()
        if not customer:
            return

        # Fetch integration token
        integration = db.query(Integration).filter(
            Integration.business_id == business_id,
            Integration.platform == customer.platform
        ).first()

        if not integration and customer.platform == "instagram":
            integration = db.query(Integration).filter(
                Integration.business_id == business_id,
                Integration.platform == "facebook"
            ).first()

        access_token = None
        meta = {}
        if integration:
            access_token = integration.access_token
            meta = integration.metadata_json or {}
        else:
            if customer.platform == "facebook":
                access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
            elif customer.platform == "instagram":
                access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
                meta = {"page_id": settings.FACEBOOK_PAGE_ID}
            elif customer.platform == "whatsapp":
                access_token = settings.WHATSAPP_ACCESS_TOKEN
                meta = {"phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID}

        # Dispatch via Messaging Service
        from app.services.messaging_service import MessagingService
        messaging_service = MessagingService()

        if customer.platform == "email":
            from app.services.email_service import send_email_as_business
            customer_email = customer.platform_user_id
            if customer_email and "@" in customer_email:
                from_email = settings.TECHSURU_IMAP_EMAIL
                from_password = settings.TECHSURU_IMAP_PASSWORD
                if from_email and from_password:
                    send_email_as_business(
                        to_email=customer_email,
                        subject="Re: TechSuru Support",
                        html_body=f"""
                        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
                            <p style="font-size: 15px; line-height: 1.6; color: #333;">{reply_text}</p>
                            <hr style="margin-top: 24px; border: none; border-top: 1px solid #eee;">
                            <p style="color: #888; font-size: 12px; margin-top: 12px;">
                                Automated AI Response · TechSuru Customer Support
                            </p>
                        </div>
                        """,
                        from_email=from_email,
                        from_password=from_password,
                        from_name="TechSuru Support"
                    )
        else:
            if access_token:
                await messaging_service.send_message(
                    platform=customer.platform,
                    access_token=access_token,
                    recipient_id=customer.platform_user_id,
                    message_text=reply_text,
                    metadata=meta
                )

        # Record auto-sent message in database as "agent" (already sent, not a draft)
        auto_msg = Message(
            conversation_id=conversation_id,
            sender_type="agent",
            content=reply_text,
            platform=customer.platform
        )
        conv.last_read_at = datetime.now(timezone.utc)
        db.add(auto_msg)
        db.commit()
        logger.info(f"✅ [AUTO MODE] Response sent and recorded for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"❌ [AUTO MODE] Failed to dispatch auto reply: {e}")


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
                message_type = "text"

                # Handle attachments (images, videos, files, audio)
                attachments = event["message"].get("attachments", [])
                if attachments:
                    for att in attachments:
                        att_type = att.get("type", "file")  # image, video, audio, file, fallback
                        att_url = att.get("payload", {}).get("url", "")

                        if att_type in ("image", "video", "audio", "file"):
                            att_message_type = att_type
                        else:
                            att_message_type = "file"

                        if att_url:
                            # Save each attachment as its own message
                            await self._handle_platform_message(
                                db,
                                platform=platform,
                                sender_id=sender_id,
                                message_text=att_url,
                                message_type=att_message_type,
                                background_tasks=background_tasks,
                                recipient_id=recipient_id
                            )
                        else:
                            # No URL — save a placeholder
                            await self._handle_platform_message(
                                db,
                                platform=platform,
                                sender_id=sender_id,
                                message_text=f"📎 [{att_type} attachment]",
                                message_type=att_message_type,
                                background_tasks=background_tasks,
                                recipient_id=recipient_id
                            )

                # Save text message if present (may be alongside attachments)
                if message_text:
                    await self._handle_platform_message(
                        db, 
                        platform=platform,
                        sender_id=sender_id,
                        message_text=message_text,
                        message_type=message_type,
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
                        message_type = "text"
                        msg_type = message.get("type", "text")

                        if msg_type == "text":
                            message_text = message["text"].get("body", "")
                        elif msg_type in ("image", "video", "audio", "document", "sticker"):
                            # Extract media info from WhatsApp Cloud API
                            media_obj = message.get(msg_type, {})
                            media_id = media_obj.get("id")
                            caption = media_obj.get("caption", "")
                            filename = media_obj.get("filename", "")

                            if msg_type == "document":
                                message_type = "file"
                            elif msg_type == "sticker":
                                message_type = "image"
                            else:
                                message_type = msg_type

                            # Try to get the actual media URL from WhatsApp Cloud API
                            media_url = ""
                            if media_id and settings.WHATSAPP_ACCESS_TOKEN:
                                try:
                                    async with httpx.AsyncClient() as client:
                                        media_res = await client.get(
                                            f"https://graph.facebook.com/v18.0/{media_id}",
                                            headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
                                        )
                                        if media_res.status_code == 200:
                                            media_url = media_res.json().get("url", "")
                                except Exception as e:
                                    logger.error(f"Failed to fetch WhatsApp media URL: {e}")

                            if media_url:
                                message_text = media_url
                            elif caption:
                                message_text = caption
                            elif filename:
                                message_text = f"📎 {filename}"
                            else:
                                message_text = f"📎 [{msg_type}]"
                        elif msg_type == "location":
                            loc = message.get("location", {})
                            lat = loc.get("latitude", "")
                            lng = loc.get("longitude", "")
                            message_text = f"📍 Location: {lat}, {lng}"
                        elif msg_type == "contacts":
                            message_text = "📇 [Contact shared]"
                        elif msg_type == "reaction":
                            # Reactions are not messages — skip
                            continue
                        else:
                            message_text = f"[{msg_type} message]"

                        if not message_text:
                            continue
                        
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
                            message_type=message_type,
                            display_name=display_name,
                            background_tasks=background_tasks
                        )

    async def _handle_platform_message(
        self, db: Session, platform: str, sender_id: str,
        message_text: str, message_type: str = "text",
        display_name: str = None,
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
        
        # Resolve effective customer ID if merged
        effective_customer_id = customer.merged_into_id if (customer and customer.is_merged and customer.merged_into_id) else customer.id

        # 3. Find or Create Conversation
        conversation = db.query(Conversation).filter(
            Conversation.customer_id == effective_customer_id,
            Conversation.business_id == business.id,
        ).order_by(Conversation.created_at.desc()).first()

        if conversation:
            # Auto-restore if it was soft-deleted
            if conversation.is_deleted:
                conversation.is_deleted = False
                conversation.deleted_at = None
                conversation.status = "open"
                db.commit()
                logger.info(f"[WEBHOOK] Auto-restored deleted conversation {conversation.id} — customer messaged again")
            # Reopen if closed/resolved
            elif conversation.status in ["closed", "resolved"]:
                conversation.status = "open"
                db.commit()
                logger.info(f"[WEBHOOK] Reopened closed/resolved conversation {conversation.id} — customer messaged again")
        else:
            conversation = Conversation(
                business_id=business.id,
                customer_id=effective_customer_id,
                status="open",
                priority="medium",
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 4. Save the Customer Message
        new_message = Message(
            conversation_id=conversation.id,
            sender_type="customer",
            content=message_text,
            message_type=message_type,
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
