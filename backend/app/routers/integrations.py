from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
import imaplib
import smtplib
from app.core.database import get_db
from app.services.oauth_service import OAuthService
from app.services.webhook_service import WebhookService
from app.services.webhook_service import WebhookService
import os
import httpx
import json
from app.core.database import SessionLocal
from app.services.rag_service import rag_service

from app.models.integration import Integration
from app.models.user import User
from app.core.dependencies import get_current_user, require_business_admin
from app.core.config import settings
from app.services.credential_service import encrypt_secret

router = APIRouter(prefix="/integrations", tags=["integrations"])
oauth_service = OAuthService()
webhook_service = WebhookService()

@router.get("")
async def list_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active integrations for the business"""
    if not current_user.business_id:
        raise HTTPException(status_code=403, detail="No business associated")
    integrations = db.query(Integration).filter(
        Integration.business_id == current_user.business_id,
        Integration.status == "active"
    ).all()
    
    return {
        "integrations": [
            {
                "platform": i.platform,
                "status": i.status,
                "created_at": i.created_at,
                "page_id": i.page_id,
                "page_name": i.page_name,
                "metadata": {
                    key: value
                    for key, value in (i.metadata_json or {}).items()
                    if key != "password_encrypted"
                },
            } for i in integrations
        ]
    }


class EmailIntegrationRequest(BaseModel):
    email: EmailStr
    app_password: str = Field(min_length=8)
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587


@router.post("/email/configure")
async def configure_email_integration(
    payload: EmailIntegrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin),
):
    """Validate and store one business's Gmail app-password connection."""
    if not current_user.business_id:
        raise HTTPException(status_code=403, detail="No business associated")

    try:
        imap = imaplib.IMAP4_SSL(
            payload.imap_host,
            payload.imap_port,
            timeout=15,
        )
        imap.login(payload.email, payload.app_password)
        imap.logout()

        with smtplib.SMTP(payload.smtp_host, payload.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(payload.email, payload.app_password)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Email connection validation failed: {exc}",
        ) from exc

    # Match on both business_id AND email so multiple inboxes per business are
    # supported. A second inbox should create a new row, not overwrite the first.
    integration = db.query(Integration).filter(
        Integration.business_id == current_user.business_id,
        Integration.platform == "email",
        Integration.page_id == payload.email.lower(),
    ).first()
    if not integration:
        integration = Integration(
            business_id=current_user.business_id,
            platform="email",
        )
        db.add(integration)

    integration.page_id = payload.email.lower()
    integration.page_name = payload.email.lower()
    integration.access_token = "encrypted-app-password"
    integration.metadata_json = {
        "email": payload.email.lower(),
        "password_encrypted": encrypt_secret(payload.app_password),
        "imap_host": payload.imap_host,
        "imap_port": payload.imap_port,
        "smtp_host": payload.smtp_host,
        "smtp_port": payload.smtp_port,
        "credential_type": "gmail_app_password",
    }
    integration.status = "active"
    db.commit()

    return {
        "platform": "email",
        "status": "active",
        "page_name": integration.page_name,
    }

PLATFORM_OAUTH_URLS = {
    "facebook": "https://www.facebook.com/v18.0/dialog/oauth",
    "instagram": "https://www.facebook.com/v18.0/dialog/oauth",
    "whatsapp": "https://www.facebook.com/v18.0/dialog/oauth",
}

@router.get("/{platform}/connect")
async def connect_platform(
    platform: str,
    current_user: User = Depends(require_business_admin),
):
    """
    Step 1: Generate OAuth URL and return it to frontend
    Frontend will redirect user to this URL
    """
    try:
        platform = platform.lower()
        if platform not in {"facebook", "instagram", "whatsapp"}:
            raise HTTPException(status_code=400, detail="Unsupported OAuth platform")
        if not current_user.business_id:
            raise HTTPException(status_code=403, detail="No business associated")
        state = jwt.encode(
            {
                "type": "integration_oauth",
                "business_id": current_user.business_id,
                "platform": platform,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        if platform == "facebook":
            auth_url = oauth_service.get_facebook_auth_url(state)
        elif platform == "instagram":
            auth_url = oauth_service.get_instagram_auth_url(state)
        elif platform == "whatsapp":
            auth_url = oauth_service.get_whatsapp_auth_url(state)
        
        return {"auth_url": auth_url, "platform": platform}
    except Exception as e:
        print(f"❌ Connect Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/callback")
async def oauth_callback(platform: str, code: str, state: str, db: Session = Depends(get_db)):
    """Resolve the authorized channel identity and persist it for one business."""
    try:
        try:
            state_data = jwt.decode(
                state,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError as exc:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state") from exc
        if (
            state_data.get("type") != "integration_oauth"
            or state_data.get("platform") != platform
        ):
            raise HTTPException(status_code=400, detail="OAuth state/platform mismatch")
        business_id = int(state_data["business_id"])

        token_data = await oauth_service.exchange_code_for_token(platform, code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        page_id = None
        page_name = None
        stored_access_token = access_token
        metadata = {}

        if platform == "facebook":
            pages = await oauth_service.discover_facebook_pages(access_token)
            if not pages:
                raise HTTPException(status_code=400, detail="No managed Facebook Page found")
            selected = pages[0]
            page_id = selected["id"]
            page_name = selected.get("name")
            stored_access_token = selected.get("access_token") or access_token
            metadata = {
                "discovered_pages": [
                    {"id": page.get("id"), "name": page.get("name")}
                    for page in pages
                ]
            }
            if not await oauth_service.enable_webhook_for_page(
                page_id, stored_access_token
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Facebook Page webhook subscription failed",
                )
        elif platform == "instagram":
            accounts = await oauth_service.discover_instagram_accounts(access_token)
            if not accounts:
                raise HTTPException(
                    status_code=400,
                    detail="No Instagram professional account linked to a managed Page",
                )
            selected = accounts[0]
            page_id = selected["instagram_account_id"]
            page_name = selected.get("username")
            stored_access_token = selected.get("page_access_token") or access_token
            metadata = {
                "instagram_account_id": page_id,
                "facebook_page_id": selected["facebook_page_id"],
                # MessagingService uses the linked Facebook Page endpoint.
                "page_id": selected["facebook_page_id"],
                "facebook_page_name": selected.get("facebook_page_name"),
            }
            if not await oauth_service.enable_webhook_for_page(
                selected["facebook_page_id"], stored_access_token
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Instagram-linked Page webhook subscription failed",
                )
        elif platform == "whatsapp":
            accounts = await oauth_service.discover_whatsapp_accounts(access_token)
            if not accounts:
                raise HTTPException(
                    status_code=400,
                    detail="No WhatsApp Business phone number found",
                )
            selected = accounts[0]
            page_id = selected["phone_number_id"]
            page_name = (
                selected.get("verified_name")
                or selected.get("display_phone_number")
            )
            metadata = {**selected, "phone_number_id": page_id}
            async with httpx.AsyncClient(timeout=20.0) as client:
                subscription = await client.post(
                    f"https://graph.facebook.com/v18.0/"
                    f"{selected['whatsapp_business_account_id']}/subscribed_apps",
                    params={"access_token": access_token},
                )
                if not subscription.is_success:
                    raise HTTPException(
                        status_code=400,
                        detail="WhatsApp webhook subscription failed",
                    )

        claimed = db.query(Integration).filter(
            Integration.platform == platform,
            Integration.page_id == page_id,
            Integration.business_id != business_id,
            Integration.status == "active",
        ).first()
        if claimed:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"This {platform} account is already connected to another "
                    "HaqDesk business"
                ),
            )

        integration = db.query(Integration).filter(
            Integration.business_id == business_id,
            Integration.platform == platform
        ).first()
        
        if not integration:
            integration = Integration(
                business_id=business_id,
                platform=platform
            )
            db.add(integration)

        integration.access_token = stored_access_token
        integration.page_id = page_id
        integration.page_name = page_name
        integration.metadata_json = metadata
        integration.status = "active"
        expires_in = token_data.get("expires_in")
        integration.expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            if expires_in else None
        )
        db.commit()
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?success={platform}")

    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error={str(e)}")

from fastapi.responses import RedirectResponse, PlainTextResponse

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Facebook webhook verification
    Facebook sends a GET request to verify the webhook URL
    """
    from app.core.config import settings
    
    # Get query parameters
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # Check if mode and token are correct
    if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        # Sanitize challenge to avoid 500 errors from malformed requests
        if challenge:
             clean_challenge = challenge.strip().replace("\\", "")
             return PlainTextResponse(content=clean_challenge, status_code=200)
        return PlainTextResponse(content="", status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receive incoming messages from Facebook/Instagram/WhatsApp
    """
    import json
    import sys
    import hmac
    import hashlib
    from app.core.config import settings
    
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Meta webhook signature validation
    app_secret = settings.FACEBOOK_CLIENT_SECRET
    if app_secret and signature:
        # Only validate if the header was actually sent (real Meta webhook)
        if not signature.startswith("sha256="):
            raise HTTPException(status_code=403, detail="Invalid signature format")
            
        expected_signature = "sha256=" + hmac.new(
            app_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
    elif not signature:
        # No signature header — allow through (dev/curl testing)
        print("⚠️  No X-Hub-Signature-256 header — skipping signature validation (dev mode)", flush=True)

    data = json.loads(body)
    
    # 🚨 FORCE PRINT TO TERMINAL
    print("\n" + "="*50, flush=True)
    print("📨 NEW WEBHOOK DATA RECEIVED!", flush=True)
    print(json.dumps(data, indent=2), flush=True)
    print("="*50 + "\n", flush=True)
    
    # Use WebhookService to process and save based on platform object
    try:
        obj = data.get("object")
        if obj == "page":
            await webhook_service.process_facebook_webhook(db, data, background_tasks)
        elif obj == "instagram":
            await webhook_service.process_instagram_webhook(db, data, background_tasks)
        elif obj == "whatsapp_business_account":
            await webhook_service.process_whatsapp_webhook(db, data, background_tasks)
        else:
            print(f"⚠️ Unknown webhook object type: {obj}")
            
    except Exception as e:
        print(f"❌ Error processing webhook: {e}", flush=True)
        # We still return 200 OK to Meta so they don't retry failed messages indefinitely
    
    return {"status": "received"}

# Alias for Instagram specific webhook to bypass caching
@router.get("/instagram_webhook")
async def verify_instagram_webhook(request: Request):
    return await verify_webhook(request)

@router.post("/instagram_webhook")
async def receive_instagram_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return await receive_webhook(request, background_tasks, db)


@router.post("/{platform}/webhook")
async def platform_webhook(platform: str, request: Request):
    """
    Specific platform webhook (e.g., /facebook/webhook)
    """
    data = await request.json()
    
    print("\n" + "="*50, flush=True)
    print(f"📨 {platform.upper()} WEBHOOK RECEIVED!", flush=True)
    print(json.dumps(data, indent=2), flush=True)
    print("="*50 + "\n", flush=True)
    
    return {"status": "received"}


