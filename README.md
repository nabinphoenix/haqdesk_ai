# HaqDesk AI

HaqDesk AI is a multi-tenant customer-support platform that brings customer messages into one workspace. It combines a shared inbox, role-based team collaboration, retrieval-augmented AI reply suggestions, business analytics, and recurring-question discovery.

This document is based on an audit of the current repository. It distinguishes implemented functionality from configuration-dependent integrations and production considerations so it is suitable as a project-submission reference.

## Project objective

Small businesses often receive customer requests through several disconnected channels, while their support knowledge and performance information live elsewhere. HaqDesk AI addresses that problem by providing a business-scoped workspace where teams can:

- receive and reply to customer conversations;
- connect Facebook Messenger, Instagram Direct, WhatsApp Cloud API, and Gmail, subject to external credentials and platform approval;
- use a knowledge base to draft grounded AI replies;
- choose review mode or automatic AI replies;
- invite supervisors and agents without sharing social-channel credentials; and
- analyse support demand, channel mix, customer attention, sentiment, and recurring FAQ opportunities.

## Implemented scope

| Area | Current implementation |
| --- | --- |
| Identity and tenants | Local authentication, Google OAuth, JWT sessions, and tenant-scoped database queries |
| Roles | `business_admin`, `supervisor`, `agent`, and `super_admin` |
| Onboarding | Newly created Google business-admin accounts complete business setup once; invited teammates join the existing business without setup |
| Unified inbox | Conversations, history, assignment, status/priority, read state, attachments, soft delete/restore, and permanent conversation deletion |
| Customer records | Per-channel customers, notes, manual linking, and customer identity merging within one business |
| AI assistance | Multilingual RAG drafts, language/sentiment-aware prompting, review/auto modes, provider fallback, and stored retrieval metadata |
| Knowledge base | PDF, DOCX, and TXT upload; tenant-scoped storage; limits; queued ingestion; Qdrant indexing; chunk inspection/editing; deletion |
| Learning loop | Approved or edited agent replies are retained as tenant-scoped retrieval examples; this is not LLM fine-tuning |
| Team collaboration | Role-based invitations, invitation revocation, membership removal, presence, and internal direct messages with WebSocket delivery |
| Integrations | Tenant-scoped Meta OAuth/webhooks for Facebook, Instagram, and WhatsApp; Gmail IMAP/SMTP connection and polling |
| Analytics | Filtered operational/channel/customer/team metrics, CSV/PDF exports, data-quality notices, and recurring FAQ discovery |
| Interface | Next.js App Router, responsive workspace navigation, light/dark themes, and a public marketing page |

## Architecture

    Browser (Next.js 16 / React 19 / TypeScript / Tailwind CSS)
                         |
                         | HTTPS API requests and internal-message WebSocket
                         v
    FastAPI application
      - authentication and role checks
      - inbox, customer, team, settings, analytics, and knowledge routers
      - Meta webhook receiver and Gmail polling worker
      - AI orchestration, retrieval, and response formatting
                         |
            +------------+-------------+
            |                          |
            v                          v
    PostgreSQL + pgvector          Qdrant
    transactional records          tenant-isolated vector collections
    and relational metadata        used for semantic retrieval
                         |
                         v
    Meta Graph API, Google OAuth, Gmail IMAP/SMTP,
    and LiteLLM-compatible LLM providers

PostgreSQL stores businesses, users, integrations, customers, conversations, messages, invitations, knowledge metadata/chunks, ingestion jobs, agent feedback, FAQ review state, and internal messages. Qdrant is the live semantic-search store. Each tenant has a collection derived from `QDRANT_COLLECTION_PREFIX` and its business ID.

The migration and preflight checks enable/check PostgreSQL `pgvector`, but the current RAG retrieval implementation uses Qdrant rather than PostgreSQL vectors. PostgreSQL is still required for application data and the current migration/preflight path.

## Repository layout

    FYP/
    ├── frontend/                     Next.js application
    │   ├── app/                      pages, layouts, and page UI
    │   ├── components/               chat, layout, marketing, and UI components
    │   ├── lib/api.ts                authenticated API helper
    │   └── public/                   logos and static assets
    ├── backend/                      FastAPI application
    │   ├── app/
    │   │   ├── auth/                 account creation and password helpers
    │   │   ├── core/                 settings, database, dependencies, preflight
    │   │   ├── models/               SQLAlchemy domain models
    │   │   ├── repositories/         analytics query layer
    │   │   ├── routers/              HTTP and WebSocket endpoints
    │   │   ├── services/             RAG, LLM, channels, analytics, and workers
    │   │   └── prompts/              controlled customer-reply prompt builder
    │   ├── tests/                    backend tests
    │   ├── migrate_db.py             schema compatibility migration
    │   ├── pyproject.toml            canonical uv dependency definition
    │   └── requirements.txt          pip-compatible dependency list
    ├── docs/diagrams/                use-case diagrams and analyses
    ├── META_INTEGRATION_GUIDE.md     Meta-specific configuration guide
    └── haqdesk_*.mmd/.svg/.png       architecture, ERD, and RAG diagrams

## Technology stack

| Layer | Technologies present in the repository |
| --- | --- |
| Frontend | Next.js 16.1.6, React 19, TypeScript, Tailwind CSS v4, Framer Motion, Lucide React, next-themes, Three.js |
| Backend | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings |
| Authentication | JWT, Passlib/bcrypt password hashing, Authlib Google OAuth |
| Relational data | PostgreSQL and SQLAlchemy; pgvector extension enabled by migration |
| Retrieval | Sentence Transformers with multilingual E5 query/passage prefixes and Qdrant |
| Generative AI | LiteLLM gateway with configurable primary and fallback models/providers |
| Documents | PyMuPDF for PDF, python-docx for DOCX, native UTF-8 text reading for TXT |
| Channels | Meta Graph API/webhooks, Gmail IMAP/SMTP, FastAPI-Mail |
| Testing | pytest/pytest-asyncio, Vitest, Testing Library, TypeScript compiler, ESLint |

The frontend uses Outfit for headings/navigation and Plus Jakarta Sans for body copy through `next/font/google`.

## Users and permissions

| Capability | Business admin | Supervisor | Agent | Super admin |
| --- | :---: | :---: | :---: | :---: |
| Work on inbox conversations | Yes | Yes | Yes | Platform-wide |
| View business analytics | Yes | Yes | No | No business-context analytics |
| View recurring FAQ opportunities | Yes | No | No | No |
| Upload/edit/delete knowledge content | Yes | No | No | Platform-wide visibility only |
| Configure business and integrations | Yes | No | No | Platform-wide visibility only |
| Invite/revoke/remove team members | Yes | No | No | Platform-wide visibility only |
| Internal direct messages | Yes | Yes | Yes | Not part of the tenant workspace |

Normal workspace queries use the authenticated user’s `business_id`. Channel webhooks route by the receiving Page/phone identity and do not fall back to an arbitrary business.

## Main workflows

### Account, onboarding, and invitations

1. A person can register locally or continue with Google.
2. A newly created Google business administrator receives a one-time `onboarding_required` flag and completes the business profile.
3. Future sign-ins do not issue that flag again merely because the person logs in.
4. A business administrator can invite an agent or supervisor by email. Acceptance joins the existing business, so teammates do not create another business or require social-channel passwords.

### Incoming customer message

1. Meta posts an event to the shared webhook, or the Gmail polling worker finds an unread email.
2. The backend resolves the recipient Page, Instagram-linked Page, or WhatsApp phone number to an active tenant integration.
3. It creates/updates the customer and conversation, persists the message, and schedules AI processing.
4. In review mode, a draft is retained for an agent to review. In auto mode, the system attempts channel delivery and only records the outgoing bubble after acceptance.
5. Stored AI metadata includes grounding state, retrieval score/source details, model/provider/fallback data, and latency when available.

### Knowledge ingestion and retrieval

1. An administrator uploads a PDF, DOCX, or TXT document.
2. Upload data is streamed to a business-scoped path while enforcing file-size, total-storage, document-count, and duplicate-checksum controls.
3. A durable database job is created. The worker retries failures up to the configured maximum and records terminal errors for the UI.
4. The document is extracted, chunked, embedded, indexed in the tenant Qdrant collection, and committed to relational metadata.
5. For a customer question, only that business’s chunks are retrieved. With no sufficiently relevant context, the result is marked ungrounded with confidence `0.0` and asks for human confirmation rather than inventing policy.

Approved/edited agent replies are stored and indexed as tenant-scoped retrieval examples. They improve future retrieval in that business but do not retrain the embedding model or LLM.

### Analytics and recurring questions

The dashboard is organised around decisions rather than a single crowded display:

- Operations: conversation/message volume, workload, response activity, sentiment, and attention queues.
- Channels: channel mix and trends for Facebook, Instagram, and email, enabling a business to see where support demand originates.
- Team: assigned-agent operational context.
- Insights: administrator-only recurring-question clusters. A cluster can be dismissed or converted into an administrator-reviewed knowledge draft.

Support analytics do not prove revenue, conversion, ROI, or lifetime value. Those claims require order, CRM, conversion, or financial-event data, which are not currently integrated.

## Prerequisites

- Node.js 20 LTS or later and npm
- Python 3.10 or later
- PostgreSQL with permission to create/use the `vector` extension
- A running Qdrant server for normal development and production
- Optional: Meta developer credentials, Google OAuth credentials, Gmail app passwords, and LLM provider keys

For Windows PowerShell, run commands from the directory shown in the prompt:

    # From C:\Users\A S U S\FYP
    python backend\migrate_db.py

    # From C:\Users\A S U S\FYP\backend
    python migrate_db.py

Similarly, from `backend` run `pip install -r requirements.txt`, not `pip install -r backend/requirements.txt`.

## Local setup

### 1. Configure the backend

From the repository root:

    cd backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip

The repository includes a locked uv project and a pip-compatible requirements file. Prefer uv when available:

    uv sync

Or use pip:

    python -m pip install -r requirements.txt

Copy the sample configuration and replace placeholders for features you will run:

    Copy-Item .env.example .env

At minimum, configure a real `DATABASE_URL` and strong random `SECRET_KEY`. Configure Qdrant and at least one working LLM provider before testing AI drafts.

### 2. Create/upgrade the database

From `backend`:

    python migrate_db.py

The migration creates known tables, enables pgvector, adds compatibility columns, and re-queues legacy documents left processing. It is a lightweight application migration rather than a full Alembic revision history; back up shared/production data before applying it.

### 3. Start the backend

    uv run uvicorn app.main:app --reload --port 8000

If you installed with pip rather than uv:

    python -m uvicorn app.main:app --reload --port 8000

Useful local endpoints:

- API root: `http://localhost:8000/`
- Preflight: `http://localhost:8000/health/preflight`
- OpenAPI UI: `http://localhost:8000/docs`

### 4. Start the frontend

In a second terminal:

    cd frontend
    npm install
    npm run dev

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL` in the frontend environment when the backend is not on `http://localhost:8000`.

## Environment configuration

Never commit `.env` files, OAuth secrets, database passwords, access tokens, or Gmail app passwords.

| Group | Key settings | Notes |
| --- | --- | --- |
| Core | `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_URL` | PostgreSQL is expected by migration/preflight |
| Google sign-in | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` | Application sign-in, not channel connection |
| Meta | `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`, `META_VERIFY_TOKEN`, `OAUTH_REDIRECT_URI` | See the Meta guide for exact callbacks |
| LLM | `LLM_PRIMARY_MODEL`, `LLM_FALLBACK_MODELS`, `LLM_FALLBACK_ENABLED`, provider API keys | LiteLLM selects primary then eligible fallbacks |
| Embeddings | `EMBEDDING_MODEL`, `EMBEDDING_DIM` | Must match existing Qdrant collections |
| Qdrant | `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION_PREFIX`, `QDRANT_ALLOW_LOCAL_FALLBACK` | Keep fallback false in shared/production environments |
| Knowledge limits | `KNOWLEDGE_UPLOAD_ROOT`, size/count/storage/extracted-text limits | Sample defaults: 10 MB/file, 100 documents, 1 GB/business |
| Workers | `KNOWLEDGE_INGESTION_*` | Current ingestion worker is an in-process background thread |
| Email | `MAIL_*` plus business email integration data | Invitation mail uses global `MAIL_*`; Gmail app passwords are encrypted in integration metadata |
| Channel sandbox | `ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX` | Defaults to false; do not enable for ordinary multi-tenant operation |

The runtime defaults in `app/core/config.py` currently select `intfloat/multilingual-e5-large` with dimension `1024`. Ensure `.env` and Qdrant collections use the same model/dimension. Model-dimension changes require planned re-indexing.

## API areas

All application APIs are under `/api/v1`, except root and preflight endpoints.

| Area | Representative routes |
| --- | --- |
| Authentication | `/auth/token`, `/auth/register`, `/auth/google`, `/auth/google/callback`, `/auth/oauth/exchange`, `/auth/me` |
| Inbox | `/inbox/conversations`, `/inbox/conversations/{id}/messages`, `/inbox/conversations/{id}/reply` |
| Customers | `/customers` plus customer linking, notes, and conversation routes |
| Knowledge | `/knowledge/upload`, `/knowledge/documents`, `/knowledge/query`, and chunk routes |
| Integrations | `/integrations`, `/{platform}/connect`, `/{platform}/callback`, `/integrations/webhook`, `/integrations/email/configure` |
| Team | `/team/invite`, member/invitation management, metrics, and member deletion |
| Analytics | `/analytics/summary`, trends, platforms, customer queues, FAQ opportunities, `/analytics/export` |
| Internal messages | `/internal-messages/*` plus `/internal-messages/ws` |
| Super admin | `/super-admin/dashboard`, stats, businesses, users, and health |

The FastAPI OpenAPI page is the authoritative live reference for schemas of the running instance.

## Verification performed during this audit

The frontend routes/components, backend routers/models/services, configuration, migration, tests, and project diagrams were reviewed.

| Check | Result |
| --- | --- |
| TypeScript compiler: `npx tsc --noEmit` | Passed |
| Focused knowledge/RAG tests previously run in this workspace | Passed: `test_rag.py` and `test_knowledge_storage.py` |
| Focused tenant-isolation/invitation tests previously run in this workspace | Passed |
| Full backend pytest suite | Did not complete during the interactive audit window; it produced no test output before cancellation, likely during heavyweight AI/test initialisation. Run in CI/local terminal before submission. |
| Frontend Vitest suite | Reported worker-start timeouts for analytics test files. |
| Frontend ESLint: `npm run lint` | Fails with 38 errors and 39 warnings at audit time, largely explicit `any`, unescaped entities, unused imports, and React hook/state-effect rules. |

The lint/test-worker findings are quality items; they should be resolved before a final production-quality deployment.

## Audit findings and recommended next steps

### High priority before production

1. Move the in-process knowledge worker and Gmail poller to separately deployed worker/queue services. The job table is durable, but a thread in every web worker is not a scalable production worker model.
2. Encrypt Meta access tokens at rest or use a managed secrets/KMS solution. Gmail app passwords are encrypted; Meta tokens are currently stored in the integration record.
3. Require a valid `X-Hub-Signature-256` signature for Meta webhooks outside explicit development mode. The current endpoint allows unsigned requests for local curl testing.
4. Replace lightweight schema changes with versioned migrations and test upgrade/rollback procedures.
5. Add rate limiting, audit logs, backups, observability, HTTPS/reverse proxy, and restricted production CORS.

### Important limitations

- OAuth selects the first discovered Page, professional Instagram account, or WhatsApp number; there is not yet an account-picker UI.
- Channel connections and automatic replies depend on valid external credentials, Meta permissions/review, and a reachable webhook URL.
- Email polling is interval-based and depends on Gmail IMAP/SMTP/app-password setup.
- Local Qdrant fallback is deliberately disabled by default and is unsuitable for multi-worker production.
- Changing the embedding model/dimension requires re-indexing; the service deliberately refuses destructive collection recreation.

## Testing and quality commands

Backend, from `backend`:

    python -m pytest -q
    python -m app.core.preflight

Frontend, from `frontend`:

    npx tsc --noEmit
    npm run lint
    npm run test
    npm run build

For a release, use passing preflight, type check, tests, lint, and production build as the minimum gate.

## Related documents

- [Meta Integration Guide](META_INTEGRATION_GUIDE.md)
- [System architecture diagram](haqdesk_system_architecture.svg)
- [Entity-relationship diagram](haqdesk_erd.svg)
- [RAG design diagram](haqdesk_rag_design.svg)
- [Use-case diagrams](docs/diagrams/use-case/)

## Security note

This is a final-year project implementation. Before processing live customer data, complete a security review covering secret rotation, data retention/deletion, consent/privacy obligations, webhook verification, encrypted backups, least-privilege database access, and provider/platform compliance.
