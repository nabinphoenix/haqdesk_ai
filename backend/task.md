# Tasks: Integrate RAG Pipeline

- [x] RAG pipeline migration - knowledge_documents and knowledge_chunks tables created
- [x] pgvector extension enabled
- [x] rag_service.py import paths fixed
- [x] knowledge.py router fully wired to rag_service
- [x] KnowledgeDocument model updated with status and business_id fields
- [x] KnowledgeChunk model updated with business_id field

- [ ] Test upload via /docs with a real PDF
- [ ] Confirm status changes from processing to ready after upload
- [ ] Verify generate-draft returns a draft when PDF is uploaded
- [ ] Wire draft reply into MessageBubble in frontend inbox
- [ ] Add BERT sentiment detection
- [ ] Add Nepali language detection and mirrored replies
