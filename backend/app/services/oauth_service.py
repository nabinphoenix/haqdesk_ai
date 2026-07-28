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
        
    def get_facebook_auth_url(self, state: str) -> str:
        """Generate Facebook OAuth URL"""
        scope = "public_profile,email,pages_show_list,pages_messaging,pages_manage_metadata"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/facebook/callback&"
            f"scope={scope}&"
            f"state={state}"
        )
    
    def get_instagram_auth_url(self, state: str) -> str:
        """Generate Instagram OAuth URL (uses same Meta Platform)"""
        scope = "pages_show_list,pages_manage_metadata,instagram_basic,instagram_manage_messages"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/instagram/callback&"
            f"scope={scope}&"
            f"state={state}"
        )
    
    def get_whatsapp_auth_url(self, state: str) -> str:
        """Generate WhatsApp OAuth URL (via Meta Business)"""
        scope = "business_management,whatsapp_business_messaging,whatsapp_business_management"
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_client_id}&"
            f"redirect_uri={self.redirect_uri}/whatsapp/callback&"
            f"scope={scope}&"
            f"state={state}"
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

    async def discover_facebook_pages(self, user_access_token: str) -> list[dict]:
        """Return managed Pages with Page IDs and Page access tokens."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/me/accounts",
                params={
                    "fields": "id,name,access_token",
                    "access_token": user_access_token,
                },
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def discover_instagram_accounts(self, user_access_token: str) -> list[dict]:
        """Return professional Instagram accounts linked to managed Pages."""
        pages = await self.discover_facebook_pages(user_access_token)
        discovered = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for page in pages:
                page_token = page.get("access_token")
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{page['id']}",
                    params={
                        "fields": "instagram_business_account{id,username,name}",
                        "access_token": page_token or user_access_token,
                    },
                )
                if not response.is_success:
                    continue
                account = response.json().get("instagram_business_account")
                if account:
                    discovered.append({
                        "instagram_account_id": account["id"],
                        "username": account.get("username") or account.get("name"),
                        "facebook_page_id": page["id"],
                        "facebook_page_name": page.get("name"),
                        "page_access_token": page_token,
                    })
        return discovered

    async def discover_whatsapp_accounts(self, user_access_token: str) -> list[dict]:
        """Return WABAs and registered phone-number IDs available to the user."""
        discovered = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            businesses = await client.get(
                "https://graph.facebook.com/v18.0/me/businesses",
                params={"access_token": user_access_token},
            )
            businesses.raise_for_status()
            for business in businesses.json().get("data", []):
                wabas = await client.get(
                    f"https://graph.facebook.com/v18.0/{business['id']}/owned_whatsapp_business_accounts",
                    params={"access_token": user_access_token},
                )
                if not wabas.is_success:
                    continue
                for waba in wabas.json().get("data", []):
                    phones = await client.get(
                        f"https://graph.facebook.com/v18.0/{waba['id']}/phone_numbers",
                        params={"access_token": user_access_token},
                    )
                    if not phones.is_success:
                        continue
                    for phone in phones.json().get("data", []):
                        discovered.append({
                            "business_manager_id": business["id"],
                            "whatsapp_business_account_id": waba["id"],
                            "whatsapp_business_name": waba.get("name"),
                            "phone_number_id": phone["id"],
                            "display_phone_number": phone.get("display_phone_number"),
                            "verified_name": phone.get("verified_name"),
                        })
        return discovered
