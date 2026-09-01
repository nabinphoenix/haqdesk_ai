# HaqDesk AI Meta Integration Guide

This guide documents the Meta channel implementation that currently exists in HaqDesk AI. It covers Facebook Messenger, Instagram Direct, and WhatsApp Cloud API connections. It is deliberately specific about what the code performs, what must be configured in Meta, and which development shortcuts must not be used in production.

For general project setup and the full implementation audit, see [README.md](README.md).

## 1. Integration model and tenant isolation

Each connected Meta channel belongs to one HaqDesk business. Its integration record stores:

- the tenant `business_id`;
- platform: `facebook`, `instagram`, or `whatsapp`;
- receiving identity: Page ID, Instagram account identity with linked Page metadata, or WhatsApp phone-number ID;
- display name, connection status, expiry information, and non-secret metadata; and
- the channel access token needed for the Graph API.

Inbound events are routed using the recipient identity in the payload. For Facebook/Instagram this is the destination Page; for WhatsApp it is the destination phone-number ID. The backend does not choose a default business when no match is found. This is the principal protection against cross-business message delivery.

Only a business administrator can start a channel OAuth connection. Agents and supervisors can see channel status but the integration-list response removes credential-like metadata from their view.

## 2. Current channel support

| Channel | OAuth discovery | Inbound messages | Outbound messages | Current constraint |
| --- | --- | --- | --- | --- |
| Facebook Messenger | Managed Facebook Pages | Shared Meta webhook | Meta Graph API | First discovered Page is selected automatically |
| Instagram Direct | Professional Instagram accounts linked to managed Pages | Shared Meta webhook | Meta Graph API through linked Page metadata | Requires a professional account linked to a Page; first result is selected |
| WhatsApp Cloud API | Business Manager → WABA → phone number | Shared Meta webhook | Cloud API send path | First discovered phone number is selected |

Gmail IMAP/SMTP is also implemented, but it is a separate business email integration and not a Meta product.

`TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` appear in the sample environment file, but the audited source has no active TikTok router or OAuth implementation. Do not claim TikTok support in the project report or deployment scope.

## 3. Exact application endpoints

With the default local backend URL (`http://localhost:8000`), use these routes:

| Purpose | Endpoint |
| --- | --- |
| List active business integrations | `GET /api/v1/integrations` |
| Start Facebook OAuth | `GET /api/v1/integrations/facebook/connect` |
| Start Instagram OAuth | `GET /api/v1/integrations/instagram/connect` |
| Start WhatsApp OAuth | `GET /api/v1/integrations/whatsapp/connect` |
| Facebook OAuth callback | `GET /api/v1/integrations/facebook/callback` |
| Instagram OAuth callback | `GET /api/v1/integrations/instagram/callback` |
| WhatsApp OAuth callback | `GET /api/v1/integrations/whatsapp/callback` |
| Main verification/event webhook | `GET/POST /api/v1/integrations/webhook` |
| Instagram webhook alias | `GET/POST /api/v1/integrations/instagram_webhook` |

Use the shared `/api/v1/integrations/webhook` endpoint for real event delivery. The generic `POST /api/v1/integrations/{platform}/webhook` route only logs and acknowledges a payload; it does not process it into the HaqDesk inbox.

## 4. Environment configuration

Create `backend/.env` from `backend/.env.example`. Never hard-code or commit a real app secret, database password, page token, WhatsApp token, or verify token.

    FACEBOOK_CLIENT_ID=your_meta_app_id
    FACEBOOK_CLIENT_SECRET=your_meta_app_secret
    META_VERIFY_TOKEN=a_long_random_value
    FRONTEND_URL=http://localhost:3000
    OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/integrations

The last setting is essential. The OAuth service appends `/{platform}/callback` to `OAUTH_REDIRECT_URI`, so the valid local redirect URLs are:

    http://localhost:8000/api/v1/integrations/facebook/callback
    http://localhost:8000/api/v1/integrations/instagram/callback
    http://localhost:8000/api/v1/integrations/whatsapp/callback

The runtime default for `OAUTH_REDIRECT_URI` is frontend-shaped. For the current integration router, override it in `.env` with the backend base shown above. If not overridden, Meta can be sent to a callback URL that FastAPI does not own.

For public hosting, use the public HTTPS API origin instead:

    FRONTEND_URL=https://app.example.com
    OAUTH_REDIRECT_URI=https://api.example.com/api/v1/integrations

Register the equivalent three HTTPS callback URLs in Meta.

## 5. Meta app configuration

The exact Meta Dashboard labels change over time, but the application-side requirements are stable:

1. Create a Meta app in Meta for Developers.
2. Add the products required for channels you will connect:
   - Facebook Login / Facebook Login for Business for the connection flow;
   - Messenger for Facebook Page messaging;
   - Instagram Graph API / Instagram Messaging for Instagram Direct;
   - WhatsApp for WhatsApp Cloud API.
3. Add all three valid OAuth callback URLs from Section 4.
4. Add the shared webhook callback URL:

       https://api.example.com/api/v1/integrations/webhook

5. Enter the exact same verification token used for `META_VERIFY_TOKEN`.
6. Subscribe the app to the product events required by the channels.
7. In development mode, add the relevant Facebook/Instagram/WhatsApp accounts as Meta app roles, testers, or test users. Invited testers must accept their invitations in Meta.
8. Before live customer use, complete the required Meta review/business verification and put the app in Live mode only after approval.

Use an HTTPS tunnel only for local testing. Do not expose an unauthenticated development server directly to the internet.

## 6. OAuth permissions requested by the code

| Connection | Requested scopes |
| --- | --- |
| Facebook | `public_profile`, `email`, `pages_show_list`, `pages_messaging`, `pages_manage_metadata` |
| Instagram | `pages_show_list`, `pages_manage_metadata`, `instagram_basic`, `instagram_manage_messages` |
| WhatsApp | `business_management`, `whatsapp_business_messaging`, `whatsapp_business_management` |

Meta may require app review, business verification, product-specific configuration, and a valid use case before granting one or more of these permissions. A scope listed in the source does not guarantee approval in all application modes.

## 7. HaqDesk connection flow

1. A signed-in business administrator starts a channel connection in Settings.
2. `GET /api/v1/integrations/{platform}/connect` creates a signed `state` token containing tenant business ID, platform, and a 15-minute expiry.
3. The browser is redirected to Meta OAuth.
4. Meta returns `code` and `state` to the configured backend callback.
5. The backend verifies `state` and exchanges the code for an access token.
6. The backend discovers the channel identity:
   - Facebook: calls `/me/accounts` and selects the first managed Page;
   - Instagram: finds `instagram_business_account` on managed Pages and selects the first result;
   - WhatsApp: discovers Business Manager accounts, WhatsApp Business Accounts, and phone numbers, then selects the first phone number.
7. The backend attempts the relevant Meta app subscription, saves the tenant-scoped integration, and redirects to:

       {FRONTEND_URL}/settings?success={platform}

8. An active Page/account/phone identity already claimed by another HaqDesk business produces an HTTP 409 conflict.

### Current limitation: account selection

The UI has no account-picker step. Administrators who manage more than one Page, professional Instagram account, or WhatsApp number should not rely on automatic first-result selection in production. Add a deliberate selection/confirmation screen before deploying that scenario.

## 8. Webhook configuration and verification

Set the Meta callback URL to:

    https://api.example.com/api/v1/integrations/webhook

Set the Meta verification token to the exact value of:

    META_VERIFY_TOKEN

During webhook verification, Meta supplies:

    hub.mode=subscribe
    hub.verify_token=...
    hub.challenge=...

The application returns the supplied challenge only when the token equals `META_VERIFY_TOKEN`; otherwise it returns HTTP 403.

For event delivery Meta sends `X-Hub-Signature-256`. When both an app secret and signature header are present, HaqDesk calculates HMAC SHA-256 using `FACEBOOK_CLIENT_SECRET` and rejects a mismatch.

### Production requirement: reject unsigned requests

The current handler permits a request with no signature header to support local curl-style testing. This is unsuitable for a public endpoint. Before production, make missing/invalid signatures fail unless an explicit local-development flag is enabled.

For Facebook and Instagram-linked Pages, the app attempts to subscribe to:

    messages,messaging_postbacks,message_reactions

For WhatsApp, it calls the chosen WhatsApp Business Account `subscribed_apps` endpoint. Confirm product-specific webhook fields in Meta Dashboard because allowed subscriptions can vary by Meta product, application mode, and permissions.

## 9. Inbound message processing

The shared webhook handles these object types:

| Meta object | Stored platform | Handling |
| --- | --- | --- |
| `page` | `facebook` | Regular and standby messaging events |
| `instagram` | `instagram` | Regular and standby messaging events |
| `whatsapp_business_account` | `whatsapp` | WhatsApp Cloud API customer messages |

For valid events, the backend:

1. ignores Page echo messages to prevent duplicate outgoing bubbles;
2. captures text, attachments/media placeholders, locations, contacts, and postbacks as applicable;
3. resolves the receiving identity to one active tenant integration;
4. creates or updates a tenant-scoped customer and conversation;
5. reopens closed/resolved/deleted conversations on a new customer message;
6. stores the customer message and schedules language detection, sentiment analysis, RAG, and the selected AI-response mode.

An unknown receiving identity is not assigned to a different business. No customer/conversation is created in that case.

## 10. Outbound replies and AI modes

An agent reply requires a valid integration for the conversation’s channel. If no integration exists, the backend returns a conflict instead of pretending that an undeliverable message was sent.

| Mode | Behavior |
| --- | --- |
| Review mode | AI produces a draft; an agent reviews, edits, and sends it. |
| Auto AI mode | AI output is sent through the connected channel automatically; the outgoing message is recorded after the platform accepts it. |

RAG responses include grounding/source metadata. If the system does not retrieve sufficiently relevant tenant knowledge, it returns an ungrounded result with confidence `0.0` and asks for human confirmation instead of treating general model knowledge as business fact.

## 11. Test plan

### Local prerequisites

1. Start PostgreSQL, Qdrant, backend, and frontend.
2. Check `http://localhost:8000/health/preflight`.
3. Expose the local webhook through a public HTTPS development tunnel if Meta must call a local machine.
4. Confirm secrets are loaded from `backend/.env`, not source code.

### Facebook Messenger

1. Connect a test Page as the intended business administrator.
2. Confirm Settings lists the Page as connected.
3. Send a message from a Meta-approved test account.
4. Confirm it appears only in that business inbox.
5. Send an agent reply and confirm it reaches the customer.
6. Repeat with a different tenant/Page to demonstrate recipient-based isolation.

### Instagram Direct

1. Use a professional Instagram account linked to a Page managed by the OAuth user.
2. Connect it through Settings.
3. Send a Direct message from a permitted tester.
4. Confirm it enters the correct business inbox and the reply is delivered through the linked Page context.

### WhatsApp Cloud API

1. Use a configured WhatsApp Business Account and permitted test number.
2. Complete the OAuth connection.
3. Send a WhatsApp test message to the configured number.
4. Confirm the phone-number recipient maps to the intended tenant.
5. Send a reply and inspect the Meta delivery/Graph API result.

### Security regressions

- Alter or expire OAuth `state`; the callback must reject it.
- Connect a Page/account/phone identity from another tenant; the second connection must conflict.
- Send a webhook with a bad signature; it must be rejected when the signature is present.
- Verify agents/supervisors cannot start a connection or retrieve connection secrets.
- Verify an unknown recipient cannot create a customer/conversation in any tenant.

## 12. Troubleshooting

| Symptom | Cause | Resolution |
| --- | --- | --- |
| Redirect URI mismatch | Redirect differs by scheme, host, path, or configured base | Register exact callback URLs and set `OAUTH_REDIRECT_URI` to the backend integration base |
| Callback reaches frontend/404 | Default OAuth redirect base was used | Set local `OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/integrations` |
| OAuth succeeds but no identity is saved | No eligible managed Page, linked professional Instagram account, or WhatsApp number | Check Meta account linkage, role, and approved permissions |
| Meta cannot verify webhook | Wrong public URL/token or unreachable HTTP endpoint | Use a public HTTPS endpoint and exact `META_VERIFY_TOKEN` |
| Meta event does not enter HaqDesk | Receiving ID is not stored as an active tenant integration | Reconnect and verify stored Page/phone identity |
| Outbound reply fails | Expired/invalid token, missing permission, wrong channel identity, or Meta policy restriction | Re-authorize and inspect backend/Meta error output |
| Wrong-business display suspected | This violates routing assumptions and is a security issue | Disable the connection, preserve logs, and investigate payload/recipient mapping immediately |

## 13. Production checklist

- [ ] Use HTTPS for frontend, API, OAuth redirects, and webhooks.
- [ ] Keep Meta app secret, access tokens, database credentials, and provider keys in a secret manager.
- [ ] Encrypt Meta access tokens at rest before production; current integration records store them directly.
- [ ] Reject unsigned/invalid webhooks outside local development.
- [ ] Use restrictive production CORS origins.
- [ ] Operate PostgreSQL backups and persistent, monitored Qdrant.
- [ ] Run ingestion/email work as managed worker services rather than per-web-process threads.
- [ ] Complete Meta app review/business verification when required.
- [ ] Publish appropriate privacy, retention, deletion, and consent policies.
- [ ] Test tenant isolation with at least two business accounts before going live.

## 14. Report-ready summary

HaqDesk AI implements a tenant-aware Meta integration architecture. A business administrator authorizes a channel, the backend records that connection for one business, and incoming Meta events are routed by their receiving Page or phone identity to that business only. The platform then creates a unified conversation, produces a knowledge-grounded AI draft or automatic reply according to business settings, and retains support data for operational analysis. Live deployment still requires Meta approval, secure public webhooks, strict signature enforcement, encrypted token storage, and scalable worker operations.
