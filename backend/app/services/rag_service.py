"""
RAG Service for HaqDesk AI
Implements document ingestion, vector storage, retrieval, and LLM generation
using LangChain, HuggingFace Embeddings, pgvector, and Groq API.
"""
import os
import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.knowledge import KnowledgeDocument, KnowledgeChunk

logger = logging.getLogger("uvicorn")

# ─── Lazy-loaded globals ───────────────────────────────────────────────
_embeddings_model = None


def _get_embeddings():
    """Lazy-load the HuggingFace embedding model (downloads ~420MB on first call)."""
    global _embeddings_model
    if _embeddings_model is None:
        logger.info("🧠 Loading HuggingFace embedding model (paraphrase-multilingual-MiniLM-L12-v2)...")
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        logger.info("✅ Embedding model loaded successfully.")
    return _embeddings_model


class RAGService:
    """Handles document ingestion, vector search, and AI response generation."""

    # ───────────────────────────────────────────────────────────────────
    # 1. DOCUMENT INGESTION
    # ───────────────────────────────────────────────────────────────────
    def _load_document_text(self, file_path: str, file_type: str) -> str:
        """Parse a file and return its full text content."""
        file_type = file_type.lower()

        if file_type == "pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

        elif file_type == "docx":
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            return "\n".join([p.text for p in doc.paragraphs])

        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _split_text(self, text_content: str) -> List[str]:
        """Split text into chunks using LangChain's RecursiveCharacterTextSplitter."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        return splitter.split_text(text_content)

    def ingest_document(
        self,
        file_path: str,
        filename: str,
        document_id: int,
        business_id: int,
        db: Session,
    ):
        """
        Full ingestion pipeline: load → split → embed → store.
        Called as a background task. Updates the document status on completion.
        """
        try:
            logger.info(f"📄 Ingesting document: {filename} (ID={document_id})")

            # Determine file type from extension
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

            # 1. Load
            raw_text = self._load_document_text(file_path, ext)
            if not raw_text.strip():
                raise ValueError("Document is empty or could not be parsed.")

            # 2. Split
            chunks = self._split_text(raw_text)
            logger.info(f"   → Split into {len(chunks)} chunks")

            # 3. Embed
            embeddings_model = _get_embeddings()
            embeddings = embeddings_model.embed_documents(chunks)
            logger.info(f"   → Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

            # 4. Store in knowledge_chunks
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                db.add(
                    KnowledgeChunk(
                        document_id=document_id,
                        business_id=business_id,
                        content=chunk_text,
                        embedding=embedding,
                        page_number=idx,
                    )
                )

            # 5. Update document status
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            if doc:
                doc.status = "ready"

            db.commit()
            logger.info(f"✅ Document '{filename}' ingested successfully ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"❌ Ingestion failed for '{filename}': {e}")
            try:
                doc = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.id == document_id
                ).first()
                if doc:
                    doc.status = "failed"
                db.commit()
            except Exception:
                pass

        finally:
            # Clean up temp file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    # ───────────────────────────────────────────────────────────────────
    # 2. VECTOR RETRIEVAL
    # ───────────────────────────────────────────────────────────────────
    def _retrieve_chunks(
        self, question: str, business_id: int, db: Session, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Embed the question and perform cosine similarity search in pgvector."""
        embeddings_model = _get_embeddings()
        query_embedding = embeddings_model.embed_query(question)

        # Convert to a PostgreSQL-compatible vector literal
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text("""
            SELECT id, content, document_id,
                   1 - (embedding <=> :query_vec ::vector) AS similarity
            FROM knowledge_chunks
            WHERE business_id = :biz_id
            ORDER BY embedding <=> :query_vec ::vector
            LIMIT :top_k
            """)

        rows = db.execute(
            sql,
            {"query_vec": embedding_str, "biz_id": business_id, "top_k": top_k},
        ).fetchall()

        results = []
        for row in rows:
            results.append({
                "chunk_id": row[0],
                "content": row[1],
                "document_id": row[2],
                "similarity": float(row[3]) if row[3] is not None else 0.0,
            })
        return results

    def retrieve_context(
        self, query: str, business_id: int, db: Session, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge base chunks filtered strictly by business_id."""
        return self._retrieve_chunks(question=query, business_id=business_id, db=db, top_k=top_k)

    # ───────────────────────────────────────────────────────────────────
    # 3. LLM GENERATION (Groq)
    # ───────────────────────────────────────────────────────────────────
    def detect_language(self, text: str) -> str:
        """Detect if the language is English, Devanagari Nepali, or Romanized Nepali."""
        try:
            from langdetect import detect
            import re
            
            text_lower = text.lower()
            
            # Check for multi-word markers first (e.g. "k xa", "k ho")
            for marker in ["k xa", "k ho"]:
                if marker in text_lower:
                    return "romanized_nepali"
            
            # Tokenize into words to avoid substring false matches (like "you" matching "yo")
            words = set(re.findall(r'\b\w+\b', text_lower))
            
            # Single-word Romanized Nepali markers
            single_word_markers = {
                "hajur", "tapai", "malai", "yo", "bhaneko", "cha", "chha", "garne",
                "bhayo", "xaina", "chaina", "gardai", "garnu", "huncha", "hudaina",
                "bhanda", "ramro", "dhanyabad"
            }
            
            if not words.isdisjoint(single_word_markers):
                return "romanized_nepali"
                
            lang = detect(text)
            if lang == "ne":
                return "nepali"
            return "english"
        except Exception:
            return "english"

    async def query(
        self,
        question: str,
        business_id: int,
        db: Session,
        confidence_threshold: float = 0.4,
        language: Optional[str] = None,
        sentiment: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        End-to-end RAG query: retrieve -> generate -> return result with confidence.
        Uses the LiteLLM gateway and isolated prompt builder.
        """
        try:
            if language is None:
                language = self.detect_language(question)

            # 1. Retrieve relevant chunks
            chunks = self._retrieve_chunks(question, business_id, db)
            if not chunks:
                logger.info("ℹ️ No knowledge chunks found for this business.")
                return None

            # 2. Check confidence (average similarity of top chunks)
            avg_similarity = sum(c["similarity"] for c in chunks) / len(chunks)
            top_similarity = chunks[0]["similarity"] if chunks else 0.0

            logger.info(f"🔍 RAG: top_similarity={top_similarity:.3f}, avg={avg_similarity:.3f}")

            if top_similarity < confidence_threshold:
                logger.info(f"ℹ️ Below confidence threshold ({confidence_threshold}). Skipping.")
                return None

            # 3. Generate response using the new LLM gateway and customer reply prompt
            from app.prompts.customer_reply_prompt import build_customer_reply_messages
            from app.services.llm_gateway import llm_gateway, LLMGatewayError
            from app.models.business import Business

            # Retrieve business details to enrich prompt if available
            business_profile = db.query(Business).filter(Business.id == business_id).first()
            business_dict = {
                "name": business_profile.name if business_profile else "our business",
                "description": getattr(business_profile, "description", "") if business_profile else ""
            } if business_profile else None

            messages = build_customer_reply_messages(
                customer_message=question,
                context_chunks=chunks,
                sentiment=sentiment,
                language=language,
                business_profile=business_dict
            )

            try:
                gateway_result = await llm_gateway.generate(messages)
                answer = gateway_result.content
                metadata = {
                    "model": gateway_result.model,
                    "provider": gateway_result.provider,
                    "fallback_used": gateway_result.fallback_used,
                    "attempts": gateway_result.attempts,
                    "latency_ms": gateway_result.latency_ms
                }
            except LLMGatewayError as ge:
                logger.error(f"❌ LLM Gateway failed: {ge}")
                answer = "AI draft could not be generated at this time. Please review the customer message manually."
                metadata = {
                    "error": str(ge),
                    "fallback_used": False,
                    "attempts": 0,
                    "failed": True
                }

            # 4. Get source document names
            doc_ids = list(set(c["document_id"] for c in chunks))
            source_docs = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id.in_(doc_ids)
            ).all()
            source_names = [d.filename for d in source_docs]

            return {
                "answer": answer,
                "confidence": round(top_similarity, 3),
                "sources": source_names,
                "chunks_used": len(chunks),
                "language_detected": language,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return None

    # ───────────────────────────────────────────────────────────────────
    # 5. CLEANUP
    # ───────────────────────────────────────────────────────────────────
    def delete_document_chunks(self, document_id: int, db: Session):
        """Remove all vector chunks belonging to a document."""
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id
        ).delete()
        db.commit()
        logger.info(f"🗑️ Deleted all chunks for document ID={document_id}")


# Singleton instance
rag_service = RAGService()
