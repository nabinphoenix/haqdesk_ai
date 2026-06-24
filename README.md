# HaqDesk AI | Project Blueprint & Status Report

## 1. Project Vision
**HaqDesk AI** is a premium, unified customer support dashboard designed to bridge the gap between businesses and their customers across multiple platforms (Facebook, Instagram, WhatsApp). The name "Haq" (हक) represents the fundamental right of every customer to receive timely, accurate, and respectful support through high-fidelity AI orchestration.

---

## 2. Technology Stack & Architecture

### **Frontend (The Neural Interface)**
- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript (Strict Typing)
- **Styling**: Tailwind CSS with custom "Neural Mesh" aesthetics.
- **Animations**: Framer Motion (for smooth, high-fidelity state transitions).
- **Icons**: Lucide React.
- **State Management**: React Hooks (useState, useEffect) with localStorage for session persistence.

### **Backend (The Intelligence Engine)**
- **Framework**: FastAPI (Python 3.10+)
- **Concurrency**: Asynchronous (AsyncIO) for high-performance I/O operations.
- **Security**: OAuth2 with JWT (JSON Web Tokens) and PBKDF2 password hashing (SHA-512).
- **Integrations**: Meta Graph API (Messenger/Instagram integration).

### **Database (The Knowledge Base)**
- **System**: PostgreSQL 18
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Manual schema synchronization with auto-startup integrity checks.

---

## 3. Project Structure
```text
FYP/
├── frontend/                 # Next.js Application
│   ├── app/                  # App Router (inbox, login, layout)
│   ├── components/
│   │   ├── chat/             # ChatWindow, MessageBubble
│   │   ├── layout/           # Unified Navbar (AppSidebar)
│   │   └── ui/               # Reusable UI elements
│   └── public/               # Static assets
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── core/             # Config, Security, Database connection
│   │   ├── models/           # SQLAlchemy DB Models (User, Message, etc.)
│   │   ├── routers/          # API Endpoints (inbox, auth, webhook)
│   │   ├── schemas/          # Pydantic Data Validation
│   │   └── services/         # Business Logic (Facebook integration)
│   └── .env                  # Environment Secrets
```

---

## 4. Installed Dependencies

### **Backend (Python)**
- `fastapi`, `uvicorn`: Web framework and server.
- `sqlalchemy`, `psycopg2-binary`: Database interaction.
- `python-jose[cryptography]`: JWT token handling.
- `passlib[bcrypt]`: Secure hashing (configured with SHA-512 fallback).
- `httpx`: Async HTTP requests for Meta API.
- `python-dotenv`: Environment variable management.

### **Frontend (Node.js)**
- `next`, `react`, `react-dom`: Core framework.
- `framer-motion`: Premium animations.
- `lucide-react`: Iconography.
- `clsx`, `tailwind-merge`: Dynamic CSS management.

---

## 5. Current Implementation Progress (What We've Done)

### **✅ Core Infrastructure**
- **Unified Auth System**: Secure login/logout flow with JWT. Created an identity mesh for "Nabin" (Admin), "Samir", and "Sita" (Representatives).
- **Database Mesh**: Established 6 core tables (`businesses`, `users`, `customers`, `integrations`, `conversations`, `messages`).
- **Meta Integration**: Functional Webhook for receiving real-time Facebook messages.

### **✅ Premium UI/UX**
- **Dynamic Inbox**: Real-time message streaming with **Optimistic UI Updates** (zero-delay messaging).
- **Responsive Layout**: A "Neural Mesh" design that protects routes automatically (Redirect Guard).
- **Identity Awareness**: The system recognizes who is logged in and logs agent responses under their specific `User ID`.

---

## 6. How the System Works Currently
1. **The Gateway**: A user logs in. The backend validates credentials and issues a JWT.
2. **The Guard**: The Frontend stores the token and grants access to protected paths like `/inbox`.
3. **The Webhook**: When a customer messages your Facebook page, Meta sends a POST request to our `/webhook` endpoint.
4. **The Intelligence**: The backend saves the message, creates/updates the conversation, and the Frontend (via polling) displays the new message instantly.
5. **The Response**: An agent (e.g., Nabin) types a reply. The UI adds it **instantly** (Optimistic Update) while the backend sends it to Facebook and logs it in PostgreSQL.

---

## 7. Upcoming Milestones (What's Next?)

### **Phase 1: Knowledge & RAG Integration (Implemented)**
- **RAG Pipeline**:
  - Document ingestion: PDF, DOCX, TXT via PyMuPDF and pypdf
  - Text chunking: LangChain RecursiveCharacterTextSplitter (500 chars, 50 overlap)
  - Embeddings: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384-dim)
  - Vector storage: PostgreSQL + pgvector extension
  - Retrieval: cosine similarity search, top-k chunks per business
  - Generation: Groq API with llama-3.3-70b-versatile
  - Multi-tenant: each business has isolated knowledge base
  - Auto-draft: incoming customer messages trigger background RAG pipeline
  - Human-in-loop: staff review/approve all AI drafts before sending

### **Phase 2: Analytics & Telemetry**
- **Live Stats**: Visualize message volume, response times, and agent performance on the `/analytics` page.
- **SLA Tracking**: Monitor if customers are getting responses within the "Haq" (Rightful) time frame.

### **Phase 3: Multi-Channel Expansion**
- **Instagram & WhatsApp**: Connect more Meta nodes to the unified inbox.
- **Team Management**: Interface for admins to manage business ID assignments (TS1, TS2, TS3).

---

## 8. Backend Upgrade: LiteLLM Gateway & uv

We have upgraded the backend to support a production-ready, multi-tenant RAG architecture with a centralized LiteLLM gateway, automatic provider fallback, rate-limit retries, and `uv`-based package management.

### **Dependency Management with uv**
Instead of plain `pip`, we use `uv` for lightning-fast package installation and locking.

**Setup & Installation:**
1. Install `uv` if you haven't already:
   ```powershell
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. Navigate to the backend directory and sync the environment:
   ```powershell
   cd backend
   uv sync
   ```
   This creates a virtual environment `.venv` and installs all dependencies from `pyproject.toml` and locks them in `uv.lock`.

### **Running the Application**
To start the backend with `uv`:
```powershell
uv run uvicorn app.main:app --reload
```

### **Running Tests & Quality Checks**
We use `pytest` for unit testing and `ruff` for linting.
```powershell
# Run the test suite
uv run python -m pytest -q

# Run ruff check for linting
uv run ruff check app tests
```

### **Preflight Verification**
Ensure the system is configured correctly and dependencies/connections are healthy:
```powershell
uv run python -m app.core.preflight
```
You can also ping the HTTP endpoint: `GET /health/preflight`

### **LLM Gateway & Provider Fallback**
The system uses a LiteLLM-powered centralized LLM gateway (`app/services/llm_gateway.py`). The RAG pipeline retrieves tenant-isolated context from PostgreSQL/pgvector and sends the structured prompt to the gateway.
- The gateway tries the primary model (`LLM_PRIMARY_MODEL` e.g., `groq/llama-3.3-70b-versatile`) first.
- If a retryable error occurs (such as a 429 rate limit, quota exhaustion, or service outage), it automatically falls back to secondary models listed in `LLM_FALLBACK_MODELS` (e.g. `gemini/gemini-2.0-flash` or `openrouter/...`).
- Custom retryable error checking ensures that bad configuration or invalid keys fail immediately instead of triggering slow timeouts, while network timeouts and rate limits trigger immediate fallback.

> [!WARNING]
> **Important Security Reminder:**
> - Never commit your `.env` file to version control.
> - Ensure all API keys and secrets remain local.

---
*Document Created: January 30, 2026*
