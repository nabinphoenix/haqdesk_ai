Implementation Plan: Configure Meta Integration for HaqDesk

This guide explains the final steps to connect your local development environment to the Meta (Facebook/Instagram/WhatsApp) Platform.

## 1. Configure Local Environment Variables (.env)
You need to update your backend `.env` file with the credentials from the Meta Dashboard.

**File Location:** `backend/.env` (Create this file if it doesn't exist)

Add the following lines:
```env
# Meta Integration Credentials
FACEBOOK_CLIENT_ID=1267944048513514
FACEBOOK_CLIENT_SECRET=YOUR_INSTAGRAM_APP_SECRET_FROM_DASHBOARD
META_VERIFY_TOKEN=YOUR_CHOSEN_VERIFY_TOKEN

# Redirect URI for OAuth
# IMPORTANT: This must point to your BACKEND, not frontend
OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/integrations
```

**Where to find values:**
- **FACEBOOK_CLIENT_ID**: Use the "Instagram App ID" you see on the dashboard (1267944048513514).
- **FACEBOOK_CLIENT_SECRET**: Click "Show" next to "Instagram app secret" in Step 1 of your screenshot.
- **META_VERIFY_TOKEN**: Any random string you chose when setting up "Configure webhooks" (Step 3). If you haven't set it, pick one now (e.g., `haqdesk_verify_123`) and use it in both `.env` and the Dashboard.

## 2. Configure Meta Dashboard Settings
Since we are using `localhost`, you must whitelist the callback URLs in the Meta Dashboard.

1.  **Go to "Step 4: Set up Instagram business login"** (from your screenshot) OR go to **Facebook Login > Settings** in the right sidebar.
2.  Enable **"Client OAuth Login"** and **"Web OAuth Login"**.
3.  In **"Valid OAuth Redirect URIs"**, add the following exact URLs:
    - `http://localhost:8000/api/v1/integrations/instagram/callback`
    - `http://localhost:8000/api/v1/integrations/facebook/callback`
    - `http://localhost:8000/api/v1/integrations/whatsapp/callback`
4.  Save Changes.

**Note:** If Meta complains about `http` (non-secure), you might need to use `https` via tools like `ngrok` or rely on "Development Mode" allowing localhost. If strictly enforced, set up ngrok and use `https://your-ngrok-url.com/api/v1/integrations...`.

## 3. Add Tester Account
Since your app is in Development Mode, you cannot log in with any Instagram account yet. You must add the specific Instagram account you want to test with.

1.  Go to **Roles > Roles** in the left sidebar.
2.  Scroll to **"Instagram Testers"**.
3.  Click **"Add Instagram Testers"**.
4.  Enter your Instagram username and invite it.
5.  **Critically Important:** Log in to that Instagram account (on web or mobile), go to **Settings > Apps and Websites > Tester Invites**, and **ACCEPT** the invite. If you don't do this, the API will fail silently.

## 4. Run the Connection
1.  Restart your backend server: `CTRL+C` then `uvicorn app.main:app --reload`.
2.  Go to your app: `http://localhost:3000/settings`.
3.  Click **Connect** on Instagram or Facebook.
4.  You should be redirected to Facebook, asked to grant permissions, and then redirected back to Settings with a "Connected" status.
