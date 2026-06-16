"""
OAuth Integration Service
Handles OAuth flows and token management for social media platforms
"""
import httpx
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings

class OAuthService:
    """Handles OAuth 2.0 flows for each platform"""
    
    def __init__(self):
        # Load from centralized config
        self.facebook_client_id = settings.FACEBOOK_CLIENT_ID
        self.facebook_client_secret = settings.FACEBOOK_CLIENT_SECRET
        self.redirect_uri = settings.OAUTH_REDIRECT_URI
        
    def get_facebook_auth_url(self, business_id: int) -> str:
        """Generate Facebook OAuth URL"""
        scope = "public_profile,email,pages_messaging"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/facebook/callback&"
            f"scope={scope}&"
            f"state={business_id}"
        )
    
    def get_instagram_auth_url(self, business_id: int) -> str:
        """Generate Instagram OAuth URL (uses same Meta Platform)"""
        scope = "instagram_basic,instagram_manage_messages"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/instagram/callback&"
            f"scope={scope}&"
            f"state={business_id}"
        )
    
    def get_whatsapp_auth_url(self, business_id: int) -> str:
        """Generate WhatsApp OAuth URL (via Meta Business)"""
        scope = "whatsapp_business_messaging,whatsapp_business_management"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/whatsapp/callback&"
            f"scope={scope}&"
            f"state={business_id}"
        )
    
    async def exchange_code_for_token(self, platform: str, code: str) -> Dict:
        """
        Exchange authorization code for access token
        This is Step 2 of OAuth flow
        """
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                token_url,
                params={
                    "client_id": self.facebook_client_id,
                    "client_secret": self.facebook_client_secret,
                    "redirect_uri": f"{self.redirect_uri}/{platform}/callback",
                    "code": code
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "access_token": data.get("access_token"),
                    "expires_in": data.get("expires_in", 3600),
                    "token_type": data.get("token_type", "Bearer")
                }
            else:
                raise Exception(f"Failed to exchange token: {response.text}")
    
    async def get_long_lived_token(self, short_token: str) -> Dict:
        """Convert short-lived token to long-lived (60 days for Facebook)"""
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.facebook_client_id,
                    "client_secret": self.facebook_client_secret,
                    "fb_exchange_token": short_token
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get long-lived token: {response.text}")

    async def enable_webhook_for_page(self, page_id: str, access_token: str) -> bool:
        """
        Crucial Step: Tell Facebook to send webhooks for this specific page to our app.
        POST /{page_id}/subscribed_apps
        """
        url = f"https://graph.facebook.com/v18.0/{page_id}/subscribed_apps"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={
                    "access_token": access_token,
                    "subscribed_fields": "messages,messaging_postbacks,message_reactions"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            else:
                print(f"⚠️ Failed to subscribe page {page_id}: {response.text}")
                return False
