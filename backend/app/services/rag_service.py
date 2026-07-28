import logging
import time
from typing import Optional, Literal
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchRequest
)
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.models.message import Message

from app.services.nepali_normalizer import normalize_nepali_text, get_embedding_input
from app.services.qa_parser import parse_qa_pairs
from app.prompts.customer_reply_prompt import build_system_prompt

logger = logging.getLogger("uvicorn")

# BAAI/bge-m3 produces 1024-dimensional embeddings
EMBEDDING_DIM = 1024
CONFIDENCE_THRESHOLD = 0.45


class RAGService:
    """
    RAG Service with BAAI/bge-m3 Multilingual Embedding & Qdrant Vector Store.
    """
    def __init__(self):
        self._embedder = None
        self._qdrant = None
        self._collection_initialized = False

    @property
    def embedder(self):
        if self._embedder is None:
            logger.info("[RAG] Loading BAAI/bge-m3 embedding model...")
            self._embedder = SentenceTransformer("BAAI/bge-m3")
            logger.info("[RAG] BAAI/bge-m3 Embedding model loaded successfully.")
        return self._embedder

    @property
    def qdrant(self):
        if self._qdrant is None:
            try:
                client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=3.0
                )
                # Test connection
                client.get_collections()
                self._qdrant = client
                logger.info(f"[RAG] Connected to Qdrant server at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as e:
                logger.warning(f"[RAG] Remote Qdrant server ({settings.QDRANT_HOST}:{settings.QDRANT_PORT}) unavailable: {e}. Falling back to embedded Qdrant (path='./qdrant_storage')...")
                self._qdrant = QdrantClient(path="./qdrant_storage")
            
            self._ensure_collection()
        return self._qdrant

    def _ensure_collection(self):
        """Create or recreate collection if dimension mismatches 1024 (BAAI/bge-m3)."""
        if self._collection_initialized:
            return
        try:
            collections = [c.name for c in self._qdrant.get_collections().collections]
            
            # Clean up old legacy collections (384-dim) if they exist
            for old_name in ["haqdesk_knowledge", "techsuru_knowledge"]:
                if old_name in collections and old_name != settings.QDRANT_COLLECTION_NAME:
                    try:
                        info = self._qdrant.get_collection(collection_name=old_name)
                        current_size = info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else None
                        if current_size != EMBEDDING_DIM:
                            logger.info(f"[RAG] Deleting legacy Qdrant collection '{old_name}'...")
                            self._qdrant.delete_collection(collection_name=old_name)
                    except Exception as e:
                        logger.warning(f"[RAG] Could not delete old collection {old_name}: {e}")

            recreate = False
            if settings.QDRANT_COLLECTION_NAME in collections:
                info = self._qdrant.get_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
                current_size = info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else None
                if current_size != EMBEDDING_DIM:
                    logger.warning(
                        f"[RAG] Qdrant collection vector size mismatch ({current_size} != {EMBEDDING_DIM}). "
                        f"Recreating collection '{settings.QDRANT_COLLECTION_NAME}' for BAAI/bge-m3..."
                    )
                    self._qdrant.delete_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
                    recreate = True

            if settings.QDRANT_COLLECTION_NAME not in collections or recreate:
                self._qdrant.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"[RAG] Initialized 1024-dim Qdrant collection '{settings.QDRANT_COLLECTION_NAME}' (BAAI/bge-m3)")
            else:
                logger.info(f"[RAG] Qdrant collection '{settings.QDRANT_COLLECTION_NAME}' ready (dim={EMBEDDING_DIM})")
            self._collection_initialized = True
        except Exception as e:
            logger.error(f"[RAG] Failed to initialize Qdrant collection: {e}")

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text using BAAI/bge-m3 after Romanized Nepali normalization."""
        normalized_input = get_embedding_input(text)
        return self.embedder.encode(normalized_input).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts using BAAI/bge-m3 after Romanized Nepali normalization."""
        normalized_inputs = [get_embedding_input(t) for t in texts]
        return self.embedder.encode(normalized_inputs).tolist()

    def detect_language(self, text: str) -> str:
        """Detect if the language is English, Devanagari Nepali, or Romanized Nepali."""
        try:
            from langdetect import detect
            import re

            text_lower = text.lower()

            for marker in ["k xa", "k ho", "k chha", "kasto xa"]:
                if marker in text_lower:
                    return "romanized_nepali"

            words = set(re.findall(r'\b\w+\b', text_lower))

            single_word_markers = {
                "hajur", "tapai", "tapailai", "malai", "yo", "bhaneko", "cha", "chha", "garne",
                "bhayo", "xaina", "chaina", "gardai", "garnu", "huncha", "hudaina",
                "bhanda", "ramro", "dhanyabad", "aahele", "aahile", "maile", "samana",
                "saman", "kina", "kinne", "milxa", "milchha", "kasari", "kasto", "xa", "parne",
                "hamro", "pauxa", "paunchha", "khoji", "ehh", "oh", "ho", "nepali"
            }

            if not words.isdisjoint(single_word_markers):
                return "romanized_nepali"

            lang = detect(text)
            if lang == "ne":
                return "nepali"
            return "english"
        except Exception:
            return "english"

    def ingest_document(
        self,
        file_path: str,
        filename: str,
        document_id: int,
        business_id: int,
        db: Session
    ):
        """Parse document into Q&A pairs (or fallback chunks), embed chunks, store in Qdrant and PostgreSQL."""
        import fitz

        logger.info(f"[RAG] Ingesting document: {filename} (ID={document_id})")

        try:
            doc = fitz.open(file_path)
            full_text_by_page = []
            full_raw_text = ""

            for page_num, page in enumerate(doc):
                p_text = page.get_text()
                full_text_by_page.append((page_num + 1, p_text))
                full_raw_text += p_text + "\n"

            doc.close()

            # Attempt Fix 2: Q&A-pair parsing
            parsed_qa = parse_qa_pairs(full_raw_text)
            chunks = []

            if parsed_qa:
                logger.info(f"[RAG] Document identified as Q&A dataset with {len(parsed_qa)} pairs.")
                # Map extracted Q&A pairs back to page numbers where possible
                for qa in parsed_qa:
                    matched_page = 1
                    for pg_num, pg_txt in full_text_by_page:
                        if qa["question"][:30] in pg_txt:
                            matched_page = pg_num
                            break
                    chunks.append({
                        "content": qa["content"],
                        "page_number": matched_page,
                    })
            else:
                logger.info(f"[RAG] No Q&A structure found. Falling back to sliding-window chunking.")
                for pg_num, pg_txt in full_text_by_page:
                    words = pg_txt.split()
                    chunk_size = 500
                    overlap = 50
                    i = 0
                    while i < len(words):
                        chunk_words = words[i:i + chunk_size]
                        chunk_text = " ".join(chunk_words).strip()
                        if chunk_text:
                            chunks.append({
                                "content": chunk_text,
                                "page_number": pg_num,
                            })
                        i += chunk_size - overlap

            logger.info(f"[RAG] Split document into {len(chunks)} total chunks.")

            if not chunks:
                raise ValueError("No text extracted from document")

            # Embed all chunks
            embeddings = self.embed_batch([c["content"] for c in chunks])
            qdrant_points = []

            for idx, (chunk_data, vector) in enumerate(zip(chunks, embeddings)):
                # Fix 3: Store metadata in PostgreSQL without embedding column
                db_chunk = KnowledgeChunk(
                    business_id=business_id,
                    document_id=document_id,
                    content=chunk_data["content"],
                    page_number=chunk_data["page_number"],
                )
                db.add(db_chunk)
                db.flush()  # Gets db_chunk.id

                # Qdrant is the sole vector store
                qdrant_points.append(
                    PointStruct(
                        id=db_chunk.id,
                        vector=vector,
                        payload={
                            "business_id": business_id,
                            "document_id": document_id,
                            "chunk_id": db_chunk.id,
                            "content": chunk_data["content"],
                            "page_number": chunk_data["page_number"],
                            "filename": filename,
                        }
                    )
                )

            db.commit()

            # Batch upsert to Qdrant
            self.qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=qdrant_points
            )

            logger.info(f"[RAG] Successfully stored {len(chunks)} Q&A chunks for doc {document_id} in Qdrant & DB")
            return len(chunks)

        except Exception as e:
            db.rollback()
            logger.error(f"[RAG] Document ingestion failed: {e}")
            raise e

        finally:
            import os
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    def retrieve_chunks(
        self,
        query_text: str,
        business_id: int,
        top_k: int = 5
    ) -> list[dict]:
        """Search Qdrant for top_k relevant chunks for a business."""
        try:
            query_embedding = self.embed_text(query_text)

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="business_id",
                        match=MatchValue(value=business_id)
                    )
                ]
            )

            if hasattr(self.qdrant, 'search'):
                results = self.qdrant.search(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    query_vector=query_embedding,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                )
            else:
                response = self.qdrant.query_points(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    query=query_embedding,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                )
                results = response.points

            chunks = []
            for result in results:
                chunks.append({
                    "content": result.payload.get("content", ""),
                    "similarity": result.score,
                    "page_number": result.payload.get("page_number"),
                    "filename": result.payload.get("filename", ""),
                    "chunk_id": result.payload.get("chunk_id"),
                    "document_id": result.payload.get("document_id"),
                })

            return chunks
        except Exception as e:
            logger.warning(f"[RAG] Qdrant search unavailable ({e}). Proceeding with general AI model knowledge.")
            return []

    async def query(
        self,
        question: str,
        business_id: int,
        db: Session,
        conversation_id: Optional[int] = None,
        current_message_id: Optional[int] = None,
        mode: Literal["auto", "review"] = "review",
        top_k: int = 5,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        language: Optional[str] = None,
        sentiment: Optional[str] = None,
        **kwargs
    ) -> Optional[dict]:
        """Full RAG pipeline: retrieve → generate → return answer with context memory."""
        start_time = time.time()

        try:
            detected_lang = language or self.detect_language(question)

            # 1. Retrieve relevant chunks
            chunks = self.retrieve_chunks(question, business_id, top_k)
            top_score = chunks[0]["similarity"] if chunks else 0.0

            sources = []
            if chunks and top_score >= confidence_threshold:
                logger.info(f"[RAG] Retrieved {len(chunks)} chunks. Top score: {top_score:.3f}")
                context = "\n\n---\n\n".join([
                    f"[Page {c['page_number']}] {c['content']}"
                    for c in chunks
                ])
                sources = list(set(c["filename"] for c in chunks if c["filename"]))
            else:
                logger.info(f"[RAG] Low confidence ({top_score:.3f}) or no chunks found for query. Using general store knowledge.")
                context = "No specific policy document match found. Answer using general helpful support knowledge for TechSuru store (electronics, laptops, mobiles, tablets, computer accessories, repairs available)."
                top_score = max(top_score, 0.75)

            # 2. Build system prompt using unified prompt builder (Fix 4)
            from app.services.llm_gateway import llm_gateway

            system_prompt = build_system_prompt(
                context=context,
                mode=mode,
                language=detected_lang,
                sentiment=sentiment
            )

            # 3. Retrieve conversation history with current_message_id exclusion (Fix 1)
            past_messages = []
            if db and conversation_id:
                history_query = db.query(Message).filter(
                    Message.conversation_id == conversation_id
                )
                if current_message_id is not None:
                    history_query = history_query.filter(Message.id != current_message_id)

                db_messages = history_query.order_by(Message.timestamp.desc()).limit(10).all()
                db_messages.reverse()
                
                for m in db_messages:
                    if not m.content:
                        continue
                    role = "user" if m.sender_type == "customer" else "assistant"
                    past_messages.append({"role": role, "content": m.content})

            messages = [{"role": "system", "content": system_prompt}]
            
            for pm in past_messages:
                messages.append(pm)
                
            # Unconditionally append current question as final user message (Fix 1)
            messages.append({"role": "user", "content": question})

            result = await llm_gateway.complete(messages=messages, max_tokens=500)

            if not result or not result.get("content"):
                logger.warning("[RAG] LLM returned empty response")
                return None

            latency_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "answer": result["content"],
                "confidence": top_score,
                "sources": sources,
                "chunks_used": len(chunks) if sources else 0,
                "language_detected": detected_lang,
                "metadata": {
                    "model": result.get("model", "unknown"),
                    "provider": result.get("provider", "unknown"),
                    "fallback_used": result.get("fallback_used", False),
                    "attempts": result.get("attempts", 1),
                    "latency_ms": latency_ms,
                }
            }

        except Exception as e:
            logger.error(f"[RAG] Query failed: {e}")
            lang = language or "english"
            fallback_answer = "Hajur! TechSuru support ma swagat xa. Tapailai laptop, mobile, accessories, kinne wa repair garne sambandhi k jankari chainchha?" if lang == "romanized_nepali" else "Hello! Welcome to TechSuru support. How can we help you today with our laptops, electronics, or repair services?"
            return {
                "answer": fallback_answer,
                "confidence": 0.5,
                "sources": [],
                "chunks_used": 0,
                "language_detected": lang,
                "metadata": {"fallback_used": True, "error": str(e)}
            }

    def delete_document_chunks(self, document_id: int, db: Session):
        """Delete all chunks for a document from both Qdrant and PostgreSQL."""
        chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id
        ).all()

        chunk_ids = [c.id for c in chunks]

        if chunk_ids:
            try:
                from qdrant_client.models import PointIdsList
                self.qdrant.delete(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points_selector=PointIdsList(points=chunk_ids)
                )
                logger.info(f"[RAG] Deleted {len(chunk_ids)} points from Qdrant")
            except Exception as e:
                logger.error(f"[RAG] Failed to delete from Qdrant: {e}")

        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id
        ).delete()
        db.commit()

    def update_chunk_embedding(self, chunk_id: int, new_content: str, db: Session):
        """Re-embed and update a single chunk in Qdrant and update content in PostgreSQL."""
        chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_id).first()
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        new_embedding = self.embed_text(new_content)

        # Update PostgreSQL content
        chunk.content = new_content
        db.commit()

        # Update Qdrant (sole vector store)
        self.qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=chunk_id,
                    vector=new_embedding,
                    payload={
                        "business_id": chunk.business_id,
                        "document_id": chunk.document_id,
                        "chunk_id": chunk_id,
                        "content": new_content,
                        "page_number": chunk.page_number,
                        "filename": "",
                    }
                )
            ]
        )
        logger.info(f"[RAG] Chunk {chunk_id} updated in Qdrant and PostgreSQL")


rag_service = RAGService()
