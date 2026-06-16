from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from jose import JWTError, jwt

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.customer import Customer
from app.models.user import User
from app.services.messaging_service import MessagingService
from app.models.integration import Integration
from app.core.config import settings


router = APIRouter(prefix="/inbox", tags=["inbox"])
messaging_service = MessagingService()

async def get_current_user(token: str, db: Session):
    """Utility to get user from token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        return None

@router.get("/conversations")
async def get_conversations(
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Fetch conversations filtered by the logged-in user's business_id"""
    print(f"Token received: {token[:20] if token else 'None'}...")
    current_user = None
    if token:
        current_user = await get_current_user(token, db)
    print(f"Current user: {current_user}")
    print(f"User business_id: {current_user.business_id if current_user else 'None'}")
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
        
    # Build query filtered by business_id
    query = db.query(Conversation)
    
    if current_user.business_id:
        # Filter by user's business
        query = query.filter(Conversation.business_id == current_user.business_id)
    elif current_user.role == "super_admin":
        # Super admin sees nothing in inbox — they use super admin dashboard
        return []
    else:
        # No valid user — return empty
        return []
    
    conversations = query.order_by(Conversation.created_at.desc()).all()
    
    result = []
    for conv in conversations:
        customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()
        
        # If merged, get the master customer to show the proper manual name
        master_customer = customer
        if customer and customer.is_merged and customer.merged_into_id:
            master = db.query(Customer).filter(Customer.id == customer.merged_into_id).first()
            if master:
                master_customer = master
                
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.timestamp.desc()).first()
        
        result.append({
            "id": conv.id,
            "customer_name": master_customer.display_name if master_customer else "Unknown",
            "customer_id": master_customer.id if master_customer else None,
            "last_message": last_message.content if last_message else "",
            "time": last_message.timestamp if last_message else conv.created_at,
            "status": conv.status,
            "platform": customer.platform if customer else "unknown", # use original platform for the icon
            "unread": 0
        })
    
    return result

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Get current user
    current_user = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass

    # Get conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # IDOR fix — verify ownership
    if current_user and current_user.business_id:
        if conversation.business_id != current_user.business_id:
            raise HTTPException(status_code=403, detail="Access denied")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.asc()).all()

    result = []
    for msg in messages:
        sender_name = None
        if msg.sender_type == "agent" and msg.sender_id:
            agent = db.query(User).filter(User.id == msg.sender_id).first()
            if agent:
                sender_name = agent.name
        elif msg.sender_type == "ai":
            sender_name = "AI Assistant"

        result.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_type": msg.sender_type,
            "sender_id": msg.sender_id,
            "sender_name": sender_name,
            "content": msg.content,
            "platform": msg.platform,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            "ai_draft": msg.ai_draft,
            "ai_language": msg.ai_language,
            "sentiment": msg.sentiment,
        })

    return result

@router.post("/conversations/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: int,
    content: str = Body(..., embed=True),
    token: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    # Require auth first
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        current_user = db.query(User).filter(User.email == email).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ownership check
    if current_user.business_id and conv.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # rest of reply logic, use current_user.id as agent_id
    agent_id = current_user.id

    customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 3. Get Integration details for token
    # NOTE: Instagram replies use the FACEBOOK Page Access Token (not INSTAGRAM_ACCESS_TOKEN).
    # The Facebook Page token is what has instagram_manage_messages permission.
    # So for Instagram, we first look for an 'instagram' integration, then fall back to 'facebook'.
    integration = db.query(Integration).filter(
        Integration.business_id == conv.business_id,
        Integration.platform == customer.platform
    ).first()
    
    # For Instagram, if no dedicated integration found, use the Facebook integration's token
    if not integration and customer.platform == "instagram":
        integration = db.query(Integration).filter(
            Integration.business_id == conv.business_id,
            Integration.platform == "facebook"
        ).first()
        if integration:
            print(f"[REPLY] No instagram integration found — falling back to Facebook Page token for Instagram reply.")

    access_token = None
    metadata = {}
    
    if integration:
        access_token = integration.access_token
        metadata = integration.metadata_json or {}
        print(f"[REPLY] Found integration for platform '{integration.platform}'. Token (first 20): {access_token[:20] if access_token else 'NONE'}...")
    else:
        # Fallback to .env settings
        print(f"[REPLY] No DB integration found — using .env fallback for platform '{customer.platform}'")
        if customer.platform == "facebook":
            access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
        elif customer.platform == "instagram":
            # CRITICAL: Use PAGE token, NOT the Instagram User token
            access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
            metadata = {"page_id": settings.FACEBOOK_PAGE_ID}
            print(f"[REPLY] Instagram reply using FACEBOOK_PAGE_ACCESS_TOKEN (not INSTAGRAM_ACCESS_TOKEN)")
        elif customer.platform == "whatsapp":
            access_token = settings.WHATSAPP_ACCESS_TOKEN
            metadata = {"phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID}
    
    print(f"[REPLY] Platform: {customer.platform} | Recipient IGSID/PSID: {customer.platform_user_id}")
    print(f"[REPLY] Final token (first 20): {access_token[:20] if access_token else 'MISSING'}...")
    
    if not access_token:
        raise HTTPException(status_code=400, detail=f"No active integration or fallback token found for {customer.platform}")

    # 4. Send via platform using MessagingService
    send_error = None
    try:
        response = await messaging_service.send_message(
            platform=customer.platform,
            access_token=access_token,
            recipient_id=customer.platform_user_id,
            message_text=content,
            metadata=metadata
        )
        # Check for errors in response (Meta returns 200 even for some errors sometimes)
        if "error" in response:
            send_error = f"Platform error: {response['error']}"
            print(f"⚠️ {send_error}")
    except Exception as e:
        send_error = f"Failed to send message: {str(e)}"
        print(f"❌ {send_error}")
    
    # 5. Save to database (Always save if we got here, so it shows in UI)
    new_message = Message(
        conversation_id=conversation_id,
        sender_type="agent",
        sender_id=agent_id,
        content=content,
        platform=customer.platform
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # If it failed to send but we saved to DB, we can return the message but with a warning 
    # Or just return the message and let the user see it in the UI.
    # To satisfy the frontend 'response.ok', we return the message. 
    # If there was an error, we can optionally include it in the response 
    # so the frontend can show a 'failed to deliver' icon.
    
    result = {
        "id": new_message.id,
        "content": new_message.content,
        "sender_type": new_message.sender_type,
        "timestamp": new_message.timestamp.isoformat(),
        "send_error": send_error
    }
    
    return result
