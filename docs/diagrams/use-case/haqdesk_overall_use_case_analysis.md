# Overall HaqDesk AI Use Case Analysis

## 1. Context & Scope

This document provides the verified architectural specification and UML 2.5 analysis for the **Overall Use Case Diagram of HaqDesk AI** (Chapter 4 – Design).

The diagram answers the core architectural questions:
1. **Who uses HaqDesk AI?**
2. **What major functionality does each actor obtain from the system?**
3. **How do external customers and communication platforms interact with the system boundary?**

---

## 2. Verified Actors & Roles

| Actor | Category | Boundary Position | Codebase Verification & Role Scope |
|---|---|---|---|
| **Business Admin** | Primary Internal Actor | Outside System Boundary | Super-user of the business tenant. Handles registration, onboarding, business profile and settings configuration, staff management (inviting, revoking, removing), communication channel integration (Meta, Gmail), knowledge base management (upload, chunking, re-indexing), analytics viewing/exporting, as well as full customer support operations. Verified in `backend/app/routers/` (`auth.py`, `team.py`, `integrations.py`, `knowledge.py`, `settings.py`, `analytics.py`, `inbox.py`). |
| **Support Staff (Agent / Supervisor)** | Primary Internal Actor | Outside System Boundary | Operational support personnel. Authenticates, accesses the Unified Inbox workspace, manages conversation statuses and priorities, inspects customer context/sentiment, uses Human-in-the-Loop AI drafting, composes manual replies, sends customer responses, uses internal team chat, and accesses business analytics (if role permitted). Modeled cleanly with `Business Admin` generalizing `Support Staff`. |
| **Customer / End User** | Primary External Actor | **Outside System Boundary** | External customer seeking assistance. Communicates exclusively via external channels (Messenger, Instagram, WhatsApp, Email). **Does not log in and has no account inside HaqDesk AI.** |
| **Communication Platform** | Secondary External Actor | **Outside System Boundary** | Generic external channel infrastructure (Meta Graph API, Gmail IMAP/SMTP, WhatsApp Cloud API) delivering incoming customer inquiries to HaqDesk webhooks/pollers and transmitting outgoing replies back to the customer. |

---

## 3. Verified Use Cases by Actor

### 3.1 Business Admin Specific Use Cases
- **Register Business Account:** Onboarding and tenant account registration (`POST /api/v1/auth/register`).
- **Log In / Authenticate:** Secure JWT authentication via email/password or Google OAuth.
- **Manage Business Profile & Settings:** Configuration of business name, contact details, operating info, and AI Response Mode (`review` vs `auto`).
- **Manage Staff:** Inviting team members, assigning roles (`agent`, `supervisor`), revoking invitations, and removing staff.
- **Configure Communication Integrations:** Connecting and authenticating Meta Page (Messenger & Instagram) and Gmail accounts.
- **Manage Knowledge Base:** Uploading business documents, previewing extracted text chunks, editing chunks with live re-indexing, testing retrieval, and deleting documents.

### 3.2 Support Staff Use Cases (Inherited & Accessible by Admin)
- **Log In / Authenticate:** Session creation and role-based authentication.
- **Access Unified Inbox:** Central multi-tenant workspace with real-time conversation cards, search, and platform filtering tabs.
- **Manage Customer Conversations:** Inspecting message timeline, viewing customer profile/identity, viewing BERT sentiment tags, updating conversation status (`open`, `pending`, `resolved`, `closed`), and adjusting priority (`low`, `medium`, `high`, `urgent`).
- **Generate AI-Assisted Response:** Inbound message triggers automatic tenant-scoped RAG knowledge retrieval and draft synthesis.
- **Review AI Draft:** Inspecting AI suggestion with grounded sources and confidence percentage.
- **Accept / Edit / Reject AI Draft:** Human-in-the-loop decision to accept, customize in composer, or discard suggested draft.
- **Write Manual Response:** Freeform text composition, file/image attachments, and voice note recording.
- **Send Customer Response:** Human-authorized outbound message dispatch to the customer.
- **Use Internal Team Chat:** Peer-to-peer and team internal collaboration chat with live presence indicators.
- **View Analytics & Export Reports:** Monitoring ticket volume, response latency, agent workload, and sentiment distribution.

### 3.3 External Customer & Communication Platform Use Cases
- **Send Message to Business:** Customer transmits inquiry from native platform.
- **Receive Business Response:** Customer receives support response in their native channel thread.
- **Deliver Incoming Customer Message:** Webhook receiver or IMAP synchronization ingests inbound payload into HaqDesk.
- **Deliver Outgoing Business Response:** Meta Send API or SMTP dispatches approved response to the platform.

---

## 4. UML `<<include>>` and `<<extend>>` Traceability

1. **`Send Message to Business` $\xrightarrow{\ll include\gg}$ `Deliver Incoming Customer Message`:** Customer message transmission necessitates platform webhook/IMAP delivery into HaqDesk.
2. **`Deliver Incoming Customer Message` $\xrightarrow{\ll include\gg}$ `Generate AI-Assisted Response`:** Inbound customer messages automatically trigger RAG context retrieval and draft generation.
3. **`Deliver Incoming Customer Message` $\xrightarrow{\ll include\gg}$ `Manage Customer Conversations`:** Inbound messages automatically create or update the unified conversation thread.
4. **`Generate AI-Assisted Response` $\xrightarrow{\ll include\gg}$ `Retrieve Business Knowledge`:** Generating an AI response incorporates semantic vector search over the business knowledge base.
5. **`Review AI Draft` $\xrightarrow{\ll extend\gg \text{ [Review Mode]}}$ `Generate AI-Assisted Response`:** Human review conditionally extends AI response generation when the business operates in Review Mode.
6. **`Accept / Edit / Reject AI Draft` $\xrightarrow{\ll include\gg}$ `Review AI Draft`:** Evaluating and deciding upon the draft is an essential component of the human review use case.
7. **`Write Manual Response` $\xrightarrow{\ll extend\gg}$ `Send Customer Response`:** Support staff can optionally write a custom response instead of using the AI-assisted draft.
8. **`Send Customer Response` $\xrightarrow{\ll include\gg}$ `Deliver Outgoing Business Response`:** Dispatching an approved customer response directly triggers outbound delivery via the corresponding platform channel.
9. **`Deliver Outgoing Business Response` $\xrightarrow{\ll include\gg}$ `Receive Business Response`:** Outbound platform delivery results in the customer receiving the response in their native app.
10. **`Export Analytics Report` $\xrightarrow{\ll extend\gg}$ `View Analytics`:** Generating CSV/PDF summary downloads extends the basic analytics dashboard viewing.

---

## 5. Excluded Incomplete / Stale Functionality

- **Super Admin Platform SaaS Governance:** Platform-level tenant provisioning and global metrics are SaaS administration concerns and are excluded from this business-tenant use case diagram.
- **Automated CRM Round-Robin Routing Engine:** The codebase utilizes a shared real-time unified inbox feed with manual assignment and status flags rather than complex automated round-robin distribution queues.
- **Third-Party CRM / Zapier Ingestion Webhooks:** Excluded as only Meta and Gmail are actively integrated.

---

## 6. Generated Artifacts

1. **High-Resolution 300 DPI Landscape PNG (9167 × 5625 px):** [`haqdesk_overall_use_case.png`](haqdesk_overall_use_case.png)
2. **Scalable Vector Graphic (SVG):** [`haqdesk_overall_use_case.svg`](haqdesk_overall_use_case.svg)
3. **Mermaid Source Diagram:** [`haqdesk_overall_use_case.mmd`](haqdesk_overall_use_case.mmd)
