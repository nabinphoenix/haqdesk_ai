"""
Messaging Service for sending messages via platform APIs
Handles message sending to Facebook, Instagram, WhatsApp, TikTok
"""
import httpx
import logging
from typing import Dict, Optional

logger = logging.getLogger("uvicorn")

class MessagingService:
    """Handles outbound messaging to social platforms"""
    
    async def send_facebook_message(self, access_token: str, recipient_id: str, message_text: str) -> Dict:
        """Send message via Facebook Messenger API"""
        url = "https://graph.facebook.com/v18.0/me/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": {"text": message_text}
        }
        
        params = {"access_token": access_token}
        
        logger.info(f"[FACEBOOK SEND] Recipient: {recipient_id}")
        logger.info(f"[FACEBOOK SEND] Token (first 20): {access_token[:20] if access_token else 'MISSING'}...")
        logger.info(f"[FACEBOOK SEND] Payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            result = response.json()
            logger.info(f"[FACEBOOK SEND] Meta response (HTTP {response.status_code}): {result}")
            return result
    
    async def send_instagram_message(self, access_token: str, recipient_id: str, message_text: str, page_id: Optional[str] = None) -> Dict:
        """
        Send message via Instagram Direct API.
        IMPORTANT: This requires the Facebook PAGE ACCESS TOKEN (the same one for Messenger),
        NOT the Instagram User Token (INSTAGRAM_ACCESS_TOKEN).
        The endpoint is POST /v18.0/{PAGE_ID}/messages with the IGSID as recipient.
        messaging_type=RESPONSE is required for replies within the 24-hour window.
        """
        from app.core.config import settings
        # Use provided page_id, fallback to settings, fallback to "me" if not available
        p_id = page_id or settings.FACEBOOK_PAGE_ID or "me"
        url = f"https://graph.facebook.com/v18.0/{p_id}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": {"text": message_text}
        }
        
        params = {"access_token": access_token}
        
        logger.info(f"[INSTAGRAM SEND] Page ID: {p_id}")
        logger.info(f"[INSTAGRAM SEND] Recipient IGSID: {recipient_id}")
        logger.info(f"[INSTAGRAM SEND] Token (first 20): {access_token[:20] if access_token else 'MISSING'}...")
        logger.info(f"[INSTAGRAM SEND] Payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            result = response.json()
            logger.info(f"[INSTAGRAM SEND] Meta response (HTTP {response.status_code}): {result}")
            return result
    
    async def send_whatsapp_message(self, access_token: str, phone_number_id: str, to: str, message_text: str) -> Dict:
        """Send message via WhatsApp Cloud API"""
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"[WHATSAPP SEND] Recipient: {to}, PhoneNumberID: {phone_number_id}")
        logger.info(f"[WHATSAPP SEND] Token (first 20): {access_token[:20] if access_token else 'MISSING'}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            logger.info(f"[WHATSAPP SEND] Meta response (HTTP {response.status_code}): {result}")
            return result
    
    async def send_message(self, platform: str, access_token: str, recipient_id: str, message_text: str, metadata: Optional[Dict] = None) -> Dict:
        """Universal message sender - routes to appropriate platform"""
        logger.info(f"[SEND] Platform detected: {platform}")
        
        if platform == "facebook":
            return await self.send_facebook_message(access_token, recipient_id, message_text)
        
        elif platform == "instagram":
            page_id = metadata.get("page_id") if metadata else None
            return await self.send_instagram_message(access_token, recipient_id, message_text, page_id=page_id)
        
        elif platform == "whatsapp":
            phone_number_id = metadata.get("phone_number_id") if metadata else None
            if not phone_number_id:
                raise ValueError("WhatsApp requires phone_number_id in metadata")
            return await self.send_whatsapp_message(access_token, phone_number_id, recipient_id, message_text)
        
        elif platform == "tiktok":
            return {"status": "not_implemented", "message": "TikTok messaging pending API approval"}
        
        else:
            raise ValueError(f"Unsupported platform: {platform}")
