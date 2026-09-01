# HaqDesk AI – Unified Inbox and Customer Support Use Case Analysis

## 1. Executive Summary & Context

This document provides a verified, code-grounded analysis and specification for the **Unified Inbox and Customer Support Use Case Diagram** of **HaqDesk AI**.

In HaqDesk AI, customer communication enters via supported external platforms (Facebook Messenger, Instagram Direct, WhatsApp, Gmail/Email). The conversations are normalized and surfaced in a single **Unified Inbox Workspace**. Internal support personnel (**Support Staff** and **Business Admin**) handle conversations with optional retrieval-augmented generation (**RAG**) AI assistance under strict **Human-in-the-Loop (HITL)** governance, and replies are dispatched back to the customer through the originating channel.

---

## 2. Verified Actor Inventory & Generalization

| Actor | Category | Boundary Position | Codebase Verification & Roles |
|---|---|---|---|
| **Support Staff (Agent)** | Primary Internal Actor | Inside System | Standard customer support agent. Accesses Unified Inbox, reads conversation histories, views customer metadata/sentiment, uses manual composer or reviews AI draft replies, and sends responses. Verified in `backend/app/routers/inbox.py` and `frontend/app/inbox/page.tsx`. |
| **Business Admin (Manager)** | Primary Internal Actor | Inside System | Inherits and generalizes all `Support Staff` operations. Possesses additional managerial privileges: soft-deleting conversations, restoring deleted conversations, permanently destroying conversations, and switching global AI Response Mode (`review` vs `auto`). Verified in `backend/app/routers/inbox.py` (`require_business_admin`) and `frontend/app/inbox/page.tsx`. |
| **Customer / End User** | Primary External Actor | **Outside System** | The individual initiating inquiries or seeking support. The customer **never** logs into HaqDesk AI and remains strictly outside the authentication perimeter. Interacts exclusively through their preferred communication channels. |
| **Communication Platform** | Secondary External Actor | **Outside System** | Generic external channel infrastructure (Meta Graph API for Facebook/Instagram, WhatsApp Cloud API, SMTP/IMAP for Email) that ingests incoming customer messages and delivers outbound business responses. |

### UML Actor Generalization:
$$\text{Business Admin} \xrightarrow{\text{generalizes}} \text{Support Staff}$$
* **Rationale:** Since `Business Admin` can execute all daily customer support workflows identical to `Support Staff` plus elevated lifecycle/configuration actions, modeling `Business Admin` as a specialization/generalization of `Support Staff` keeps the diagram clean and adheres to standard UML 2.5 reuse patterns.

---

## 3. Verified Use Case Inventory & Code Traceability

### 3.1 External Customer & Channel Operations (Outside Boundary)
- **Send Message to Business:** Customer transmits a message using an external communication channel (`messenger`, `instagram`, `whatsapp`, `email`).
- **Receive Business Response:** Customer receives the business reply inside their native channel client.
- **Deliver Incoming Message:** Inbound webhook / polling ingestion receives raw payload, normalizes sender/content, updates conversation thread, and triggers AI drafting (`backend/app/services/webhook_service.py`).
- **Deliver Outgoing Response:** Outbound dispatcher transmits human-approved message via channel-specific API or SMTP (`backend/app/routers/inbox.py::reply_to_conversation`, `send_attachment`).

### 3.2 Unified Inbox Workspace & Discovery
- **Access Unified Inbox:** Authenticated users open the multi-tenant inbox workspace (`frontend/app/inbox/page.tsx`, `backend/app/routers/inbox.py::get_conversations`).
- **View Conversations:** Real-time list of conversation cards showing customer name, platform badge, preview snippet, unread counter, and timestamp.
- **Search / Filter Conversations:** (`<<extend>> View Conversations`) Dynamic keyword filtering and single-click platform tabs (`All`, `WhatsApp`, `Facebook`, `Instagram`, `Email`).
- **Select Conversation:** User chooses an active conversation thread from the feed to load detailed context and timeline.

### 3.3 Conversation Inspection & Metadata Intelligence
When a conversation is selected (`<<include>>`):
- **View Conversation History:** Chronological chat transcript with sender role tags (`customer`, `agent`, `ai`), timestamps, attachment previews, and voice message audio players (`frontend/components/chat/ChatWindow.tsx`).
- **View Customer Details:** Customer identity, email, phone, avatar, and linked cross-platform identities (`frontend/components/chat/CustomerSidebar.tsx`, `backend/app/routers/customers.py`).
- **View Channel Information:** Channel origin indicator (e.g., Messenger, Instagram, WhatsApp, Email).
- **View Sentiment:** BERT-analyzed sentiment indicator (`positive`, `neutral`, `negative`) displayed per message and thread.
- **View Priority & Attention Information:** Priority badges (`low`, `medium`, `high`, `urgent`), unread activity counters, and sound/toast alerts for new messages.

### 3.4 Conversation Curation & Lifecycle
- **Update Conversation Status:** Support agents can update conversation state to `open` or `pending`; Admins can resolve or close (`PATCH /api/v1/inbox/conversations/{id}`).
- **Update Conversation Priority:** Adjust priority level (`low`, `medium`, `high`, `urgent`) to escalate critical customer threads.
- **Maintain Customer Notes:** Internal staff notes saved on the customer profile for cross-agent handover (`POST /api/v1/customers/{id}/notes`).
- **Delete / Restore Conversation:** (`Business Admin` only) Soft-delete conversation, view deleted threads, restore accidentally removed threads, or permanently purge (`DELETE/POST /api/v1/inbox/conversations/{id}`).

### 3.5 AI Assistance & Human-in-the-Loop (HITL) Workflow
- **Generate AI-Assisted Response:** Ingestion triggers tenant-scoped RAG vector search over uploaded knowledge documents and generates grounded draft responses (`backend/app/services/rag_service.py`, `backend/app/services/webhook_service.py`).
- **Review AI Draft:** (`<<extend>> [Review Mode] Generate AI-Assisted Response`) Suggestion banner (`AISuggestionBox.tsx`) presents grounded draft, retrieval sources, and confidence score.
- **Accept / Edit / Reject AI Draft:** (`<<include>> Review AI Draft`)
  - **Accept:** Loads AI draft directly into reply composer / readies for instant dispatch.
  - **Edit:** Transfers draft into text area for human tweaking, personalization, or tone adjustment.
  - **Reject / Dismiss:** Discards suggested response.
- **Write Manual Response:** Staff composes freeform text, attaches documents/images, or records voice notes (`ChatWindow.tsx`).
- **Send Customer Response:** Human-authorized transmission triggered by the agent. Includes `Deliver Outgoing Response`.
- **Automatically Dispatch AI Reply:** (`<<extend>> [Auto AI Mode] Generate AI-Assisted Response`) Optional business setting where high-confidence AI drafts bypass human review and dispatch automatically.

---

## 4. Human-in-the-Loop (HITL) Verification

```
                      ┌────────────────────────────────────────┐
                      │ External Customer Message Arrives       │
                      └──────────────────┬─────────────────────┘
                                         ▼
                      ┌────────────────────────────────────────┐
                      │ Ingestion & Sentiment Analysis          │
                      │ + RAG Knowledge Grounding              │
                      └──────────────────┬─────────────────────┘
                                         ▼
                               /───────────────────\
                              <  AI Response Mode?  >
                               \───────────────────/
                               /                   \
                   [Review Mode]                   [Auto AI Mode]
                         /                               \
                        ▼                                 ▼
         ┌──────────────────────────────┐    ┌──────────────────────────────┐
         │ AI Draft Displayed in Inbox  │    │ AI Draft Dispatched Directly │
         │ (AISuggestionBox Component)  │    │ to Customer via Channel API  │
         └──────────────┬───────────────┘    └──────────────────────────────┘
                        ▼
         ┌──────────────────────────────┐
         │ Human Support Staff Review   │
         │ - Inspect Grounded Sources   │
         │ - Evaluate Context & Tone    │
         └──────────────┬───────────────┘
                        ▼
         ┌────────────────────────────────────────────────────────┐
         │ Human Decision:                                        │
         │   ├─ Accept Draft  ───────► Populate / Ready Dispatch │
         │   ├─ Edit Draft    ───────► Refine in Composer       │
         │   ├─ Reject Draft  ───────► Dismiss Suggestion       │
         │   └─ Manual Write  ───────► Compose Custom Reply     │
         └──────────────────────┬─────────────────────────────────┘
                                ▼
         ┌────────────────────────────────────────────────────────┐
         │ Human Clicks "Send" ──► Outbound API / SMTP Delivery   │
         └────────────────────────────────────────────────────────┘
```

---

## 5. Artifacts Generated

1. **Mermaid Diagram File:** [`haqdesk_unified_inbox_use_case.mmd`](haqdesk_unified_inbox_use_case.mmd)
2. **Standard Academic Vector SVG:** [`haqdesk_unified_inbox_use_case.svg`](haqdesk_unified_inbox_use_case.svg)
3. **High-Resolution 300 DPI Landscape PNG:** [`haqdesk_unified_inbox_use_case.png`](haqdesk_unified_inbox_use_case.png)
