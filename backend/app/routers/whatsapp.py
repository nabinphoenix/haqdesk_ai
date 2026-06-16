import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Body, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User

from app.core.config import settings
from app.core.database import get_db
from app.services.webhook_service import WebhookService
from app.services.messaging_service import MessagingService
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

logger = logging.getLogger("uvicorn")

whatsapp_service = WebhookService()
messaging_service = MessagingService()

@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    print(f"Expected: '{settings.WHATSAPP_VERIFY_TOKEN}', Got: '{verify_token}'")
    if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=challenge or "")
    raise HTTPException(status_code=403, detail="Invalid verification token")

@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Receive incoming WhatsApp messages and process them.
    Delegates to existing WebhookService logic which saves messages and triggers AI reply.
    """
    import hmac
    import hashlib
    import json
    
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    app_secret = settings.FACEBOOK_CLIENT_SECRET
    
    if app_secret:
        if not signature.startswith("sha256="):
            raise HTTPException(status_code=403, detail="Invalid signature format")
            
        expected_signature = "sha256=" + hmac.new(
            app_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)
    await whatsapp_service.process_whatsapp_webhook(db, payload, background_tasks)
    return {"status": "received"}

class WhatsAppSendRequest(BaseModel):
    conversation_id: int
    message: str

@router.post("/send")
async def send_message(
    request: WhatsAppSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a WhatsApp message for a given conversation.
    Looks up the customer phone number and uses MessagingService.
    """
    conversation_id = request.conversation_id
    message = request.message
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    customer = db.query(Customer).filter(Customer.id == conversation.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.platform != "whatsapp":
        raise HTTPException(status_code=400, detail="Conversation is not a WhatsApp conversation")

    access_token = settings.WHATSAPP_ACCESS_TOKEN
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    if not access_token or not phone_number_id:
        raise HTTPException(status_code=500, detail="WhatsApp credentials not configured")

    try:
        await messaging_service.send_message(
            platform="whatsapp",
            access_token=access_token,
            recipient_id=customer.platform_user_id,
            message_text=message,
            metadata={"phone_number_id": phone_number_id},
        )
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")

    new_msg = Message(
        conversation_id=conversation_id,
        sender_type="agent",
        content=message,
        platform="whatsapp",
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return {"id": new_msg.id, "content": new_msg.content, "timestamp": new_msg.timestamp.isoformat()}
