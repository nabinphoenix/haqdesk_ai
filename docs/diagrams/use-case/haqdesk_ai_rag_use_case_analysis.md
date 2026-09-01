# HaqDesk AI - AI-Assisted Response and RAG use-case diagram

This diagram describes the RAG-assisted response workflow in HaqDesk AI. Support Staff is the primary actor; Business Admin inherits staff actions and can also test knowledge retrieval. Customers and communication platforms are external actors.

## Main flow

1. A customer sends a message through a communication platform.
2. HaqDesk receives the message, retrieves business knowledge and conversation context, and generates an AI response draft.
3. In review mode, staff can inspect sources, confidence, and sentiment before accepting, editing, rejecting, or replacing the draft.
4. An approved response is delivered through the platform to the customer. In auto mode, the generated response can be dispatched directly.

## Files

- [Mermaid source](haqdesk_ai_rag_use_case.mmd)
- [SVG diagram](haqdesk_ai_rag_use_case.svg)
- [PNG diagram](haqdesk_ai_rag_use_case.png)
