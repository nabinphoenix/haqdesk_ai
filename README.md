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

### **Phase 1: Knowledge & RAG Integration**
- **Knowledge Base**: Build the interface to upload PDFs/Docs.
- **RAG Engine**: Integrate FAISS or PGVector to allow the AI to "read" your business documents and suggest replies to agents.

### **Phase 2: Analytics & Telemetry**
- **Live Stats**: Visualize message volume, response times, and agent performance on the `/analytics` page.
- **SLA Tracking**: Monitor if customers are getting responses within the "Haq" (Rightful) time frame.

### **Phase 3: Multi-Channel Expansion**
- **Instagram & WhatsApp**: Connect more Meta nodes to the unified inbox.
- **Team Management**: Interface for admins to manage business ID assignments (TS1, TS2, TS3).

---
*Document Created: January 30, 2026*
