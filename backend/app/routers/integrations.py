from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
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

router = APIRouter(prefix="/integrations", tags=["integrations"])
oauth_service = OAuthService()
webhook_service = WebhookService()

@router.get("")
async def list_integrations(business_id: int = 1, db: Session = Depends(get_db)):
    """List all active integrations for the business"""
    integrations = db.query(Integration).filter(
        Integration.business_id == business_id,
        Integration.status == "active"
    ).all()
    
    return {
        "integrations": [
            {
                "platform": i.platform,
                "status": i.status,
                "created_at": i.created_at,
                "metadata": i.metadata_json
            } for i in integrations
        ]
    }

PLATFORM_OAUTH_URLS = {
    "facebook": "https://www.facebook.com/v18.0/dialog/oauth",
    "instagram": "https://www.facebook.com/v18.0/dialog/oauth",
    "whatsapp": "https://www.facebook.com/v18.0/dialog/oauth",
}

@router.get("/{platform}/connect")
async def connect_platform(platform: str, business_id: int = 1):
    """
    Step 1: Generate OAuth URL and return it to frontend
    Frontend will redirect user to this URL
    """
    try:
        platform = platform.lower()
        if platform == "facebook":
            auth_url = oauth_service.get_facebook_auth_url(business_id)
        elif platform == "instagram":
            auth_url = oauth_service.get_instagram_auth_url(business_id)
        elif platform == "whatsapp":
            auth_url = oauth_service.get_whatsapp_auth_url(business_id)
        else:
            # Fallback for unsupported platforms or mock
            return {"auth_url": f"{PLATFORM_OAUTH_URLS.get(platform, '')}?mock=true&business_id={business_id}"}
        
        return {"auth_url": auth_url, "platform": platform}
    except Exception as e:
        print(f"❌ Connect Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/callback")
async def oauth_callback(platform: str, code: str, state: str, db: Session = Depends(get_db)):
    """
    Step 2: Receive authorization code from platform and exchange for access token
    """
    print(f"🔄 OAuth Callback received for {platform}. Code: {code[:10]}... State: {state}")
    try:
        business_id = int(state)
        
        # 2. Exchange 'code' for access token using platform's token endpoint
        token_data = await oauth_service.exchange_code_for_token(platform, code)
        access_token = token_data.get("access_token")
        
        if not access_token:
             print("❌ No access_token returned from exchange.")
             raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        print(f"✅ Access Token retrieved: {access_token[:10]}...")

        # 3. Store token in Database (Integration model)
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
        
        integration.access_token = access_token
        integration.status = "active"
        # integration.expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        
        db.commit()
        db.refresh(integration)
        print(f"✅ Integration saved to DB for {platform}")

        # 5. NEW: Automatically Subscribe Page to Webhooks
        # We need to find the Page ID first. For Instagram, it's linked to a Page.
        if platform in ["facebook", "instagram"]:
            try:
                # Fetch Pages this user manages
                async with httpx.AsyncClient() as client:
                    pages_res = await client.get(
                        "https://graph.facebook.com/v18.0/me/accounts",
                        params={"access_token": access_token}
                    )
                    if pages_res.status_code == 200:
                        data = pages_res.json()
                        for page in data.get("data", []):
                            # Subscribe EACH page found (including the one linked to IG)
                            pid = page.get("id")
                            p_token = page.get("access_token") # Use Page Token if available
                            await oauth_service.enable_webhook_for_page(pid, p_token)
                            print(f"📢 Subscribed Page {pid} to Webhooks")
            except Exception as e:
                print(f"⚠️ Warning: Auto-subscribe failed: {e}")
        
        # 6. Redirect back to frontend
        from app.core.config import settings
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?success={platform}")
        
    except Exception as e:
        print(f"❌ OAuth Callback Error: {e}")
        from app.core.config import settings
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


