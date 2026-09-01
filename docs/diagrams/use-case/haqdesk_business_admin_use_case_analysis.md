# HaqDesk AI – Business Administration use-case audit

## Scope and actor

The primary actor is **Business Admin**. The actor is a tenant-scoped `business_admin` user with a `business_id`.

The repository also implements a distinct `super_admin` role and `/super-admin/*` dashboard, but that role is platform-level: it aggregates all businesses, users, messages, conversations, documents, integrations, and system health. It has no business context and is explicitly excluded from the **HaqDesk AI – Business Administration** boundary.

## Verified capabilities included in the diagram

| Area | Verified capability | Implementation evidence |
| --- | --- | --- |
| Authentication and business account | Register Business | `POST /api/v1/auth/register` creates a new `Business` and first `business_admin`; `frontend/app/register/page.tsx` |
| Authentication and business account | Login / Logout | `POST /api/v1/auth/token`, Google OAuth, and `POST /api/v1/auth/logout`; `frontend/app/login/page.tsx`, `frontend/components/layout/AppSidebar.tsx` |
| Authentication and business account | Manage Business Profile | `GET/PATCH /api/v1/settings/business` updates business name, contact details, website, and description; `frontend/app/settings/page.tsx` |
| Authentication and business account | Manage Settings | Business AI response mode (`review`/`auto`) is persisted through the settings API; settings UI is available to Business Admin |
| Staff management | View Staff and Presence | `GET /api/v1/team/metrics` and `GET /api/v1/team/members` return tenant-scoped members and online/offline status; `frontend/app/team/page.tsx` |
| Staff management | Invite Staff | `POST /api/v1/team/invite` creates a tenant-scoped invitation and returns a link/email result; team UI provides the invite form |
| Staff management | Assign Role during Invitation | The invitation payload accepts Agent, Supervisor, or Admin and stores the mapped role; post-invite role editing is not claimed |
| Staff management | Remove Staff | `DELETE /api/v1/team/members/{user_id}` is admin-only and tenant-scoped; team UI exposes the remove action |
| Communication integrations | Access Integration Settings | Business Admin settings UI loads the integrations tab; `GET /api/v1/integrations` returns active integrations for the business |
| Communication integrations | Connect Meta Channels | Business-admin OAuth flow supports Facebook, Instagram, and WhatsApp; `GET /api/v1/integrations/{platform}/connect` and OAuth callback persist the integration |
| Communication integrations | Connect Gmail | `POST /api/v1/integrations/email/configure` validates and stores a Gmail IMAP/SMTP app-password connection; settings UI provides the form |
| Communication integrations | View Integration Status | Active integration records and status are returned by `GET /api/v1/integrations` and displayed in settings |
| Communication integrations | Update / Reconnect Integration | Re-running Meta OAuth or Gmail configuration updates the existing business integration record and marks it active |
| Knowledge base | Access Knowledge Base | Business Admin has the `/knowledge` route; the page loads documents and knowledge configuration |
| Knowledge base | Upload Documents | `POST /api/v1/knowledge/upload` accepts PDF, DOCX, and TXT files and returns `processing` status |
| Knowledge base | View Documents and Processing Status | `GET /api/v1/knowledge/documents` returns document status and chunk counts; the page displays the state |
| Knowledge base | Search Knowledge | `POST /api/v1/knowledge/query` performs a tenant-scoped knowledge query; the Knowledge page exposes a test/query interface |
| Knowledge base | Delete Document | `DELETE /api/v1/knowledge/documents/{document_id}` is business-admin-only and removes the stored document/chunks |
| Knowledge base | Update / Re-index Document Content | `GET /documents/{id}/chunks` plus `PATCH /chunks/{id}` lets the admin edit a chunk and re-index it. This is not presented as full-document reprocessing |
| Customer support | Access Unified Inbox | `GET /api/v1/inbox/conversations` returns non-deleted conversations for the current business across supported channels; `frontend/app/inbox/page.tsx` |
| Customer support | View Customer Conversations | Conversation message history is returned by `/api/v1/inbox/conversations/{id}/messages` and rendered by `ChatWindow` |
| Customer support | View Customer Information | `CustomerSidebar` loads `/api/v1/customers/{id}` and customer conversation history |
| Customer support | Generate AI-Assisted Response | Incoming messages trigger the webhook background service, which queries the tenant knowledge base and stores an AI draft; the chat UI displays the suggestion |
| Customer support | Review / Edit / Dismiss AI Draft | `AISuggestionBox` and `MessageBubble` expose accept/use, edit, and dismiss behavior in review mode; there is no durable reject state |
| Customer support | Write Manual Response | `ChatWindow` provides a manual compose field, with subject support for email conversations |
| Customer support | Send Customer Response | `POST /api/v1/inbox/conversations/{id}/reply` sends text through email or Meta channels and records the reply; attachments are also supported |
| Analytics and collaboration | View Analytics and Export Reports | Business Admin and Supervisor are allowed by `require_business_analytics`; analytics UI calls summary, trend, platform/customer views, and CSV/PDF export endpoints |
| Analytics and collaboration | Internal Chat | Tenant-scoped internal threads/messages support start, history, send, read, and live updates; `frontend/app/messages/page.tsx` |

## Excluded proposed or incomplete capabilities

- **Super Admin / platform administration**: a real role and dashboard exist, but they are outside business administration and not mixed into this boundary.
- **Update Staff after invitation**: no member `PATCH`/`PUT` operation or UI for changing name, email, or role.
- **Assign Role as a post-invite operation**: only role selection during invitation is implemented, so the diagram labels the included behavior accordingly.
- **Enable / Disable Staff**: no admin operation changes a member's account status; online/offline is presence, not enable/disable.
- **Disconnect Integration**: no disconnect endpoint or settings action is implemented.
- **Full-document reprocessing**: only per-chunk update/re-index is implemented.
- **Rejecting an AI draft as a durable workflow state**: the UI supports dismissing/hiding a draft, but there is no persisted reject operation; the diagram uses “Dismiss” for accuracy.
- **Notification preferences/alerts as a working service**: the settings toggles are local-storage UI state and have no notification consumer; they are not included. Staff presence is included because it is persisted, heartbeated, and rendered.
- **JWT generation, SQL, embeddings, Qdrant filtering, webhook mechanics, and WebSocket connection creation**: implementation details, not Business Admin use cases.

## Relationship interpretation

- `Invite Staff` **includes** `Assign Role during Invitation` because the role is selected as part of creating an invitation.
- `Invite Staff` and `Remove Staff` are optional extensions of the staff roster/presence view.
- `Access Integration Settings` **includes** `View Integration Status`; connecting or reconnecting a channel is an optional extension of that settings flow.
- `Access Knowledge Base` **includes** viewing documents/status; upload, query, update/re-index, and delete are optional extensions of the page's base access.
- `Access Unified Inbox` **includes** viewing customer conversations; viewing customer information, generating a draft, and sending a response are optional extensions of the inbox/conversation flow. `Review / Edit / Dismiss AI Draft` is an optional extension of that generated-draft flow.
- `Write Manual Response` is an optional extension of sending a customer response because a response may instead be populated from an AI draft.

The diagram source is [haqdesk_business_admin_use_case.mmd](haqdesk_business_admin_use_case.mmd), and the rendered high-resolution diagram is [haqdesk_business_admin_use_case.png](haqdesk_business_admin_use_case.png) with an editable vector version at [haqdesk_business_admin_use_case.svg](haqdesk_business_admin_use_case.svg).
