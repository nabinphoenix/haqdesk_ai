# HaqDesk AI – Communication Channel Integration Use Case Analysis

## 1. Executive Summary & Architectural Scope

This document provides the verified analysis and UML 2.5 specification for the **Communication Channel Integration Use Case Diagram** in **HaqDesk AI**.

The diagram provides a clear demarcation between:
1. **Actively Demonstrated Channels in the Final Year Project (FYP):** Facebook Messenger, Instagram Direct, and Gmail.
2. **Architectural Extensibility to Additional Eligible Channels:** WhatsApp Business API and generic external channel infrastructure, which remain supported by the underlying data models and webhook parsers but require formal Meta Business Verification and permissions for live activation.

---

## 2. Active Channels Verified from Code

| Channel | Protocol / Provider | Auth Mechanism | Inbound / Outbound Implementation |
|---|---|---|---|
| **Facebook Messenger** | Meta Graph API / Webhooks | Facebook OAuth (Page Access Token) | • **Inbound:** Webhook endpoint `/integrations/webhook` receives `page` events ([`webhook_service.py`](file:///c:/Users/A%20S%20U%20S/FYP/backend/app/services/webhook_service.py)).<br>• **Outbound:** Meta Send API delivers messages to PSID recipient. |
| **Instagram Direct** | Meta Graph API / Webhooks | Facebook Page OAuth (`instagram_manage_messages`) | • **Inbound:** Webhook endpoint `/integrations/webhook` receives `instagram` events.<br>• **Outbound:** Meta Send API delivers messages to IGSID recipient. |
| **Gmail / Support Email** | IMAP & SMTP Services | Gmail App Password (AES-256 encrypted) | • **Inbound:** Periodic IMAP poller synchronizes unread emails and customer threads ([`email_service.py`](file:///c:/Users/A%20S%20U%20S/FYP/backend/app/services/email_service.py)).<br>• **Outbound:** Secure TLS SMTP dispatches branded customer support replies. |

---

## 3. Admin Configuration Capabilities & RBAC

- **Authorized Actor:** `Business Admin` (Sole authorized human actor).
  - Routes in [`backend/app/routers/integrations.py`](file:///c:/Users/A%20S%20U%20S/FYP/backend/app/routers/integrations.py) enforce `require_business_admin` on `/{platform}/connect` and `/email/configure`.
  - Frontend Settings (`/settings`) restricts the **Integrations** tab to `business_admin`.
- **Verified Admin Use Cases:**
  - **Access Integration Settings:** View active channels, connection statuses, connected page names, and expiration metadata.
  - **Configure Communication Channel:** Select channel type and initiate authentication flow.
  - **Connect Meta Integration:** Authorize Facebook Page and Instagram Professional Account via Meta dialog.
  - **Connect Gmail / Email Account:** Submit email and App Password with instant TLS test verification.
  - **Authenticate / Authorize Integration:** Exchange OAuth code for permanent page tokens or validate email credentials.
  - **Verify Integration Connection:** Live connection handshake testing during setup.
  - **View Integration Status:** Monitor active channel health and page metadata.
  - **Update Integration Settings:** Re-authenticate or update channel configuration.
  - **Disconnect Integration:** Revoke access token, delete local credentials, and mark status inactive.

---

## 4. Operational Inbound & Outbound Behavior

- **Receive Customer Message:** Ingestion hub receives external inbound messages from Meta webhooks or Gmail IMAP polling.
- **Process Meta Communication:** Parses raw Meta webhook JSON payloads, extracts sender IDs and media attachments.
- **Retrieve Gmail Messages:** Fetches unread customer inquiries from the configured IMAP mailbox.
- **Synchronize Customer Messages:** Maps external platform user identifiers (PSID, IGSID, Email) to unified customer profiles and conversation threads.
- **Send Customer Response:** Outbound message dispatching via Meta Graph API or SMTP based on conversation channel origin.

---

## 5. Architectural Extension Capability & Excluded Features

- **Architectural Extension (WhatsApp Business):**
  - Data model (`Integration.platform = "whatsapp"`) and webhook handlers exist in the backend codebase.
  - In the FYP sandbox, the Meta test business is **non-business-verified**, meaning live WhatsApp Cloud API phone numbers cannot be provisioned without official business documentation.
  - Modeled as a distinct **dashed extension use case** with the explicit note: *"Additional eligible channels are subject to business verification and platform permissions."*
- **Excluded Low-Level Details:**
  - Webhook route URLs (`/api/v1/integrations/webhook`), ngrok tunnels, Graph API version tags (`v18.0`), IMAP/SMTP port numbers (993/587), and encrypted token strings are omitted from the functional diagram.

---

## 6. Generated Artifacts

1. **High-Resolution 300 DPI Landscape PNG (9167 × 5625 px):** [`haqdesk_channel_integration_use_case.png`](haqdesk_channel_integration_use_case.png)
2. **Scalable Vector Graphic (SVG):** [`haqdesk_channel_integration_use_case.svg`](haqdesk_channel_integration_use_case.svg)
3. **Mermaid Source Diagram:** [`haqdesk_channel_integration_use_case.mmd`](haqdesk_channel_integration_use_case.mmd)
