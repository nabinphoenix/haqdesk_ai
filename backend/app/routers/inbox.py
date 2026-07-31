from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form, Request
import os
import httpx
import uuid
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from jose import JWTError, jwt

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.customer import Customer
from app.models.user import User
from app.services.messaging_service import MessagingService
from app.models.integration import Integration
from app.models.business import Business
from app.core.config import settings


router = APIRouter(prefix="/inbox", tags=["inbox"])
messaging_service = MessagingService()

from app.core.dependencies import get_current_user, require_business_admin

@router.get("/conversations")
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch conversations filtered by the logged-in user's business_id"""
        
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
    
    # Filter out soft-deleted conversations
    query = query.filter(Conversation.is_deleted == False)
    conversations = query.all()
    
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

        # Unread = customer messages that arrived after the conversation was last marked read
        if conv.last_read_at:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.sender_type == "customer",
                Message.timestamp > conv.last_read_at
            ).count()
        else:
            unread_count = db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.sender_type == "customer"
            ).count()
        
        sort_time = last_message.timestamp if last_message else conv.created_at

        result.append({
            "id": conv.id,
            "customer_name": master_customer.display_name if master_customer else "Unknown",
            "customer_email": master_customer.platform_user_id if master_customer and master_customer.platform == "email" else None,
            "customer_id": master_customer.id if master_customer else None,
            "last_message": last_message.content if last_message else "",
            "last_message_sender_type": last_message.sender_type if last_message else None,
            "time": sort_time,
            "status": conv.status,
            "priority": conv.priority,
            "platform": customer.platform if customer else "unknown", # use original platform for the icon
            "unread": unread_count,
            "assigned_agent_id": conv.assigned_agent_id
        })

    # Sort by most recent activity, newest first
    result.sort(key=lambda x: x["time"], reverse=True)
    
    return result

@router.post("/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    conversation.last_read_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "marked_read", "last_read_at": conversation.last_read_at.isoformat()}

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

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
            "message_type": msg.message_type or "text",
            "platform": msg.platform,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            "ai_draft": msg.ai_draft,
            "ai_language": msg.ai_language,
            "sentiment": msg.sentiment,
            "ai_metadata": msg.ai_metadata,
        })

    return result

class ReplyRequest(BaseModel):
    content: str
    subject: Optional[str] = "Re: Support from TechSuru"

@router.post("/conversations/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: int,
    request: ReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = request.content
    subject = request.subject or "Re: Support from TechSuru"

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
        print(f"[REPLY] Found integration for platform '{integration.platform}'.")
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

    
    # 4. Send via platform
    send_error = None

    if customer.platform == "email":
        from app.services.email_service import send_email_as_business
        from app.services.credential_service import get_business_email_credentials

        customer_email = customer.platform_user_id
        if customer_email and "@" in customer_email:
            credentials = get_business_email_credentials(db, conv.business_id)
            if not credentials:
                send_error = "Business email not configured"
            else:
                business = db.query(Business).filter(
                    Business.id == conv.business_id
                ).first()
                sent = send_email_as_business(
                    to_email=customer_email,
                    subject=subject,
                    html_body=f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
                        <p style="font-size: 15px; line-height: 1.6; color: #333;">{content}</p>
                        <hr style="margin-top: 24px; border: none; border-top: 1px solid #eee;">
                        <p style="color: #888; font-size: 12px; margin-top: 12px;">
                            Sent via HaqDesk AI · TechSuru Customer Support
                        </p>
                    </div>
                    """,
                    from_email=credentials["email"],
                    from_password=credentials["password"],
                    from_name=(
                        f"{business.name} Support"
                        if business else "Customer Support"
                    ),
                    smtp_host=credentials["smtp_host"],
                    smtp_port=credentials["smtp_port"],
                )
                if not sent:
                    send_error = "Failed to send email reply"
        else:
            send_error = "No valid email address for customer"
    else:
        # Non-email platforms (Facebook, Instagram, WhatsApp)
        if not access_token:
            raise HTTPException(status_code=400, detail=f"No active integration or fallback token found for {customer.platform}")

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
    conv.last_read_at = datetime.now(timezone.utc)
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
        "error": send_error
    }
    
    return result


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Soft delete — just mark as deleted, never remove from DB
    conversation.is_deleted = True
    conversation.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Conversation moved to deleted"}


@router.post("/conversations/{conversation_id}/restore")
async def restore_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    conversation.is_deleted = False
    conversation.deleted_at = None
    db.commit()

    return {"message": "Conversation restored"}


@router.get("/conversations/deleted")
async def get_deleted_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.business_id:
        return []

    conversations = db.query(Conversation).filter(
        Conversation.business_id == current_user.business_id,
        Conversation.is_deleted == True
    ).all()

    result = []
    for conv in conversations:
        customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.timestamp.desc()).first()

        result.append({
            "id": conv.id,
            "customer_name": customer.display_name if customer else "Unknown",
            "customer_id": customer.id if customer else None,
            "last_message": last_message.content if last_message else "",
            "platform": customer.platform if customer else "unknown",
            "deleted_at": conv.deleted_at.isoformat() if conv.deleted_at else None,
            "status": conv.status,
            "priority": conv.priority,
        })

    result.sort(key=lambda x: x["deleted_at"] or "", reverse=True)
    return result


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    customer = db.query(Customer).filter(Customer.id == conversation.customer_id).first()

    # If merged, get the master customer to show the proper manual name and email
    master_customer = customer
    if customer and customer.is_merged and customer.merged_into_id:
        master = db.query(Customer).filter(Customer.id == customer.merged_into_id).first()
        if master:
            master_customer = master

    return {
        "id": conversation.id,
        "customer_name": master_customer.display_name if master_customer else "Unknown",
        "customer_email": master_customer.platform_user_id if master_customer and master_customer.platform == "email" else None,
        "customer_id": master_customer.id if master_customer else None,
        "status": conversation.status,
        "priority": conversation.priority,
        "platform": customer.platform if customer else "unknown",
    }


class ConversationUpdateRequest(BaseModel):
    priority: Optional[str] = None
    status: Optional[str] = None

@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    payload: ConversationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    allowed_priorities = ["low", "medium", "high", "urgent"]
    allowed_statuses = ["open", "pending", "resolved", "closed"]

    if payload.priority:
        if payload.priority not in allowed_priorities:
            raise HTTPException(status_code=400, detail=f"Priority must be one of {allowed_priorities}")
        conversation.priority = payload.priority

    if payload.status:
        if payload.status not in allowed_statuses:
            raise HTTPException(status_code=400, detail=f"Status must be one of {allowed_statuses}")
        if current_user.role not in ("business_admin", "super_admin") and payload.status not in ("open", "pending"):
            raise HTTPException(
                status_code=403,
                detail="Agents may only set conversation status to open or pending",
            )
        conversation.status = payload.status

    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "priority": conversation.priority,
        "status": conversation.status
    }


@router.post("/conversations/{conversation_id}/attachment")
async def send_attachment(
    conversation_id: int,
    request: Request,
    file: UploadFile = File(...),
    message: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    message_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.business_id and conversation.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get customer info
    customer = db.query(Customer).filter(Customer.id == conversation.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get business integration for this platform
    integration = db.query(Integration).filter(
        Integration.business_id == conversation.business_id,
        Integration.platform == customer.platform,
        Integration.status == "active"
    ).first()

    # Save file locally first
    upload_dir = "uploads/attachments"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    send_error = None
    platform = customer.platform

    # Determine if this is a voice message
    is_voice = (message_type == "voice") or (file_ext in ("webm", "mp3", "ogg", "wav"))

    # ── FACEBOOK ─────────────────────────────────────────────
    if platform == "facebook":
        if not integration:
            send_error = "No active integration found"
        else:
            access_token = integration.access_token
            recipient_id = customer.platform_user_id

            # Determine file type for Meta API
            image_exts = {"jpg", "jpeg", "png", "gif", "webp"}
            video_exts = {"mp4", "mov", "avi"}
            audio_exts = {"webm", "mp3", "ogg", "wav", "m4a"}

            if file_ext in image_exts:
                attachment_type = "image"
            elif file_ext in video_exts:
                attachment_type = "video"
            elif file_ext in audio_exts or is_voice:
                attachment_type = "audio"
            else:
                attachment_type = "file"

            # Step 1: Upload file to Meta attachment upload API
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    upload_url = "https://graph.facebook.com/v18.0/me/message_attachments"

                    # For Facebook — upload attachment first
                    with open(file_path, "rb") as f_data:
                        upload_response = await client.post(
                            upload_url,
                            params={"access_token": access_token},
                            data={
                                "message": f'{{"attachment":{{"type":"{attachment_type}","payload":{{"is_reusable":true}}}}}}'
                            },
                            files={"filedata": (file.filename, f_data, file.content_type or "application/octet-stream")}
                        )

                    upload_data = upload_response.json()
                    print(f"[ATTACHMENT] Upload response: {upload_data}")

                    if "attachment_id" in upload_data:
                        attachment_id = upload_data["attachment_id"]

                        # Step 2: Send message with attachment_id
                        send_response = await client.post(
                            f"https://graph.facebook.com/v18.0/me/messages",
                            params={"access_token": access_token},
                            json={
                                "recipient": {"id": recipient_id},
                                "message": {
                                    "attachment": {
                                        "type": attachment_type,
                                        "payload": {"attachment_id": attachment_id}
                                    }
                                }
                            }
                        )
                        send_data = send_response.json()
                        print(f"[ATTACHMENT] Send response: {send_data}")

                        if "error" in send_data:
                            send_error = send_data["error"].get("message", "Meta API error")
                        elif message:
                            # Send caption message as a separate text message
                            caption_response = await client.post(
                                f"https://graph.facebook.com/v18.0/me/messages",
                                params={"access_token": access_token},
                                json={
                                    "recipient": {"id": recipient_id},
                                    "message": {"text": message}
                                }
                            )
                            caption_data = caption_response.json()
                            print(f"[ATTACHMENT] Caption send response: {caption_data}")

                    else:
                        send_error = upload_data.get("error", {}).get("message", "Upload failed")

            except Exception as e:
                send_error = str(e)
                print(f"[ATTACHMENT] Exception: {e}")

    # ── INSTAGRAM ─────────────────────────────────────────────
    elif platform == "instagram":
        if not integration:
            send_error = "No active integration found"
        else:
            access_token = integration.access_token
            recipient_id = customer.platform_user_id

            # Determine media type for Meta API
            image_exts = {"jpg", "jpeg", "png", "gif", "webp"}
            video_exts = {"mp4", "mov", "avi"}
            audio_exts = {"webm", "mp3", "ogg", "wav", "m4a"}

            if file_ext in image_exts:
                attachment_type = "image"
            elif file_ext in video_exts:
                attachment_type = "video"
            elif file_ext in audio_exts or is_voice:
                attachment_type = "audio"
            else:
                attachment_type = "file"

            # Construct public URL using the base URL of the incoming request
            base_url = str(request.base_url).rstrip("/")
            public_file_url = f"{base_url}/uploads/attachments/{unique_filename}"
            if is_voice:
                public_file_url = f"{base_url}/audio/{unique_filename}"

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Send media via public URL
                    send_response = await client.post(
                        f"https://graph.facebook.com/v18.0/me/messages",
                        params={"access_token": access_token},
                        json={
                            "recipient": {"id": recipient_id},
                            "message": {
                                "attachment": {
                                    "type": attachment_type,
                                    "payload": {"url": public_file_url}
                                }
                            }
                        }
                    )
                    send_data = send_response.json()
                    print(f"[ATTACHMENT] Instagram URL send response: {send_data}")

                    if "error" in send_data:
                        send_error = send_data["error"].get("message", "Meta API error")
                    elif message:
                        # Send caption message as a separate text message
                        caption_response = await client.post(
                            f"https://graph.facebook.com/v18.0/me/messages",
                            params={"access_token": access_token},
                            json={
                                "recipient": {"id": recipient_id},
                                "message": {"text": message}
                            }
                        )
                        caption_data = caption_response.json()
                        print(f"[ATTACHMENT] Instagram Caption send response: {caption_data}")

            except Exception as e:
                send_error = str(e)
                print(f"[ATTACHMENT] Instagram exception: {e}")

    # ── EMAIL ──────────────────────────────────────────────────
    elif platform == "email":
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email import encoders
        from app.services.credential_service import get_business_email_credentials

        customer_email = customer.platform_user_id
        credentials = get_business_email_credentials(db, conversation.business_id)
        from_email = credentials["email"] if credentials else None
        from_password = credentials["password"] if credentials else None

        if not from_email or not from_password:
            send_error = "Business email not configured"
        elif not customer_email or "@" not in customer_email:
            send_error = "Invalid customer email"
        else:
            try:
                msg = MIMEMultipart()
                msg["Subject"] = subject or "File from HaqDesk Support"
                msg["From"] = f"HaqDesk Support <{from_email}>"
                msg["To"] = customer_email
                msg.attach(MIMEText(message or "Please find the attached file from HaqDesk Support.", "plain"))

                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={file.filename}")
                    msg.attach(part)

                with smtplib.SMTP(
                    credentials["smtp_host"],
                    credentials["smtp_port"],
                ) as server:
                    server.starttls()
                    server.login(from_email, from_password)
                    server.sendmail(from_email, customer_email, msg.as_string())

                print(f"[ATTACHMENT] Email with attachment sent to {customer_email}")
            except Exception as e:
                send_error = str(e)
                print(f"[ATTACHMENT] Email attachment error: {e}")

    # ── WHATSAPP ────────────────────────────────────────────────
    elif platform == "whatsapp":
        send_error = "WhatsApp file sending not yet implemented"

    if send_error:
        print(f"[ATTACHMENT] Delivery failed: {send_error}")
        raise HTTPException(status_code=400, detail=f"Delivery failed: {send_error}")

    # Determine message_type based on file extension
    image_exts = {"jpg", "jpeg", "png", "gif", "webp"}
    video_exts = {"mp4", "mov", "avi"}
    audio_exts = {"webm", "mp3", "ogg", "wav", "m4a"}

    if is_voice:
        agent_message_type = "voice"
    elif file_ext in image_exts:
        agent_message_type = "image"
    elif file_ext in video_exts:
        agent_message_type = "video"
    elif file_ext in audio_exts:
        agent_message_type = "audio"
    else:
        agent_message_type = "file"

    message_content = "🎤 Voice message" if is_voice else f"/uploads/attachments/{unique_filename}"
    audio_url = f"http://localhost:8000/audio/{unique_filename}" if is_voice else None

    # ── Save message record since delivery succeeded ──────
    new_message = Message(
        conversation_id=conversation_id,
        sender_type="agent",
        sender_id=current_user.id,
        content=message_content,
        platform=platform,
        message_type=agent_message_type,
        ai_metadata={
            "filename": file.filename,
            "audio_url": audio_url
        }
    )
    db.add(new_message)

    # If there is also a text caption, save it as a separate message
    if message and not is_voice:
        caption_message = Message(
            conversation_id=conversation_id,
            sender_type="agent",
            sender_id=current_user.id,
            content=message,
            platform=platform,
            message_type="text"
        )
        db.add(caption_message)

    db.commit()
    db.refresh(new_message)

    return {
        "message_id": new_message.id,
        "filename": file.filename,
        "content": new_message.content,
        "message_type": new_message.message_type,
        "ai_metadata": new_message.ai_metadata,
        "delivered": True,
        "is_voice": is_voice,
        "audio_url": audio_url,
    }

