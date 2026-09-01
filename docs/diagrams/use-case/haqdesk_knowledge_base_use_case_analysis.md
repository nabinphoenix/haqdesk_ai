# HaqDesk AI – Knowledge Base Management Use Case Analysis

## 1. Context & Scope

This document provides the code-verified specification and architectural rationale for the **Knowledge Base Management Use Case Diagram** in **HaqDesk AI**.

In HaqDesk AI, business knowledge powers the Retrieval-Augmented Generation (RAG) assistant. The Knowledge Base Management domain encompasses document lifecycle operations (upload, validation, parsing, chunking, and embedding), document inspection, inline chunk editing, cascading deletion, and interactive testing of knowledge retrieval.

---

## 2. Actor Verification & RBAC Isolation

| Actor | Category | Boundary | RBAC & Codebase Traceability |
|---|---|---|---|
| **Business Admin** | Primary Authorized Actor | Inside System Boundary | The sole human role authorized to manage the knowledge base. <br>• **Backend Route Protection:** [`backend/app/routers/knowledge.py`](file:///c:/Users/A%20S%20U%20S/FYP/backend/app/routers/knowledge.py) strictly enforces `require_business_admin` on document uploads, deletions, and chunk edits.<br>• **Frontend Navigation Protection:** [`frontend/components/layout/AppSidebar.tsx`](file:///c:/Users/A%20S%20U%20S/FYP/frontend/components/layout/AppSidebar.tsx) exposes the `/knowledge` route exclusively to `roles: ["business_admin"]`. |
| **Support Staff (Agent)** | *Excluded from KB Management* | Inside System Boundary | Support Staff / Agents use retrieved knowledge transparently inside the Unified Inbox workspace, but **do not possess RBAC permissions to upload, edit, re-index, or delete knowledge documents**. Excluded from this specific diagram to maintain strict RBAC accuracy. |

---

## 3. Verified User-Facing Operations

### 3.1 Document Ingestion & Management
- **Access Knowledge Base:** Business Admin opens `/knowledge` to view the document inventory, ingestion overview, and aggregate metrics.
- **Upload Knowledge Document:** Admin selects and submits business files (supported extensions: `.pdf`, `.docx`, `.txt`, maximum size 10MB).
- **Delete Knowledge Document:** Admin permanently removes a document. Triggers a database cascade and automatically purges all corresponding vectors from the vector index (`DELETE /api/v1/knowledge/documents/{document_id}`).

### 3.2 Catalog Inspection & Status Monitoring
- **View Uploaded Documents:** Live table displaying document filename, file format badge, calculated file size, chunk count, and upload timestamp (`GET /api/v1/knowledge/documents`).
- **View Document Details:** Modal/sheet inspection displaying document metadata and processing summary.
- **View Processing Status:** Real-time polling indicator reflecting the background ingestion pipeline (`processing`, `ready`, `failed`).
- **Search Knowledge Documents:** Client-side filter to quickly locate documents by filename or keyword.

### 3.3 Knowledge Chunk Curation & Maintenance
- **Preview Knowledge Chunks:** Explores extracted text chunks and associated page-number mappings for a selected document (`GET /api/v1/knowledge/documents/{document_id}/chunks`).
- **Search Knowledge Chunks:** In-modal keyword search across all extracted chunks of a document.
- **Edit Knowledge Chunk:** Admin can directly edit the text of any chunk inline. Saving automatically triggers re-embedding and updates the vector database (`PATCH /api/v1/knowledge/chunks/{chunk_id}`).

### 3.4 Interactive Retrieval Testing (Test Sandbox)
- **Test Knowledge Retrieval (Ask Knowledge Question):** Admin enters natural-language test queries to verify RAG response quality before serving customers (`POST /api/v1/knowledge/query`).
- **View Generated Answer:** Inspects the synthesized response generated from the business knowledge base.
- **View Retrieved Sources & Citations:** Displays the specific document name citations and grounding chunks used by the engine.
- **View Confidence Match %:** Displays the semantic similarity percentage score for the retrieved chunks.

---

## 4. Automatic Supporting Behaviors (System Pipeline)

The system automatically performs these tasks as part of the primary user-facing use cases:
1. **Validate Document:** (`<<include>> Upload Knowledge Document`) Verifies that file extension is `.pdf`, `.docx`, or `.txt`, payload is non-empty, and size is $\le$ 10MB.
2. **Process Document Content:** (`<<include>> Upload Knowledge Document`) Asynchronous background task extracts text, normalizes content, parses Q&A pairs, and creates semantic chunks.
3. **Index Business Knowledge:** (`<<include>> Process Document Content` and `<<include>> Edit Knowledge Chunk`) Generates dense embeddings and writes points into the tenant's isolated vector collection.
4. **Purge Vector Embeddings:** (`<<include>> Delete Knowledge Document`) Synchronously removes all associated chunk points from the vector store to prevent stale retrieval.

---

## 5. Excluded Stale / Low-Level Implementation Details

As per standard UML functional use-case principles and user guidelines, the following are intentionally excluded:
- **Low-level algorithmic internals:** Vector dimension parameters (384/1024), Cosine distance metric, embedding model names (E5, multilingual-e5-small), Qdrant collection prefixes (`haqdesk_biz_X`), text chunk overlap windows, and tokenizers.
- **Planned / Stale features not implemented in codebase:**
  - *Standalone Reprocess Document button:* Not implemented (ingestion is fully automatic on upload; chunk-level edits re-index immediately).
  - *Folder / Batch multi-file drag-drop upload:* Single-file upload is currently enforced.
  - *Web Scraping / URL Knowledge Ingestion:* Not implemented.

---

## 6. Generated Artifacts

1. **High-Resolution 300 DPI PNG (9167 × 5625 px, Landscape):** [`haqdesk_knowledge_base_use_case.png`](haqdesk_knowledge_base_use_case.png)
2. **Standard Academic Vector SVG:** [`haqdesk_knowledge_base_use_case.svg`](haqdesk_knowledge_base_use_case.svg)
3. **Mermaid Source Diagram:** [`haqdesk_knowledge_base_use_case.mmd`](haqdesk_knowledge_base_use_case.mmd)
