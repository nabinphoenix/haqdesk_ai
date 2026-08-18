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
from app.models.business import Business

from app.services.nepali_normalizer import normalize_nepali_text, get_embedding_input
from app.services.qa_parser import parse_qa_pairs
from app.prompts.customer_reply_prompt import build_system_prompt
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger("uvicorn")

# Embedding dimension — must match the model configured in settings
EMBEDDING_DIM = settings.EMBEDDING_DIM
CONFIDENCE_THRESHOLD = 0.45


class RAGService:
    """
    RAG Service with multilingual embedding (intfloat/multilingual-e5-small by default)
    & Qdrant Vector Store.
    """
    def __init__(self):
        self._embedder = None
        self._qdrant = None
        self._initialized_collections = set()

    @property
    def embedder(self):
        if self._embedder is None:
            model_name = settings.EMBEDDING_MODEL
            logger.info("[RAG] Loading %s embedding model...", model_name)
            self._embedder = SentenceTransformer(model_name)
            logger.info("[RAG] %s embedding model loaded successfully.", model_name)
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
            
        return self._qdrant

    @staticmethod
    def collection_name_for_business(business_id: int) -> str:
        """Derive the only allowed Qdrant collection name for a tenant."""
        if not isinstance(business_id, int) or isinstance(business_id, bool) or business_id <= 0:
            raise ValueError("A positive integer business_id is required")
        prefix = settings.QDRANT_COLLECTION_PREFIX.strip().strip("_")
        if not prefix:
            raise ValueError("QDRANT_COLLECTION_PREFIX cannot be blank")
        return f"{prefix}_{business_id}"

    def _collection_exists(self, business_id: int) -> bool:
        collection_name = self.collection_name_for_business(business_id)
        if collection_name in self._initialized_collections:
            return True
        exists = self.qdrant.collection_exists(collection_name=collection_name)
        if exists:
            self._initialized_collections.add(collection_name)
        return exists

    def _ensure_business_collection(self, business_id: int) -> str:
        """Lazily create one non-destructive collection for a business."""
        collection_name = self.collection_name_for_business(business_id)
        if not self._collection_exists(business_id):
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("[RAG] Created business collection '%s'", collection_name)

        info = self.qdrant.get_collection(collection_name=collection_name)
        vectors = info.config.params.vectors
        current_size = vectors.size if hasattr(vectors, "size") else None
        if current_size != EMBEDDING_DIM:
            raise RuntimeError(
                f"Qdrant collection '{collection_name}' has vector size "
                f"{current_size}; expected {EMBEDDING_DIM}. Refusing destructive recreation."
            )
        self._initialized_collections.add(collection_name)
        return collection_name

    def embed_text(self, text: str, prefix: str = "query: ") -> list[float]:
        """Embed a single text after Romanized Nepali normalization.

        Args:
            text: Raw input text.
            prefix: E5-family models require a task prefix.
                    Use "query: " for search queries (default),
                    "passage: " for document chunks during ingestion.
        """
        normalized_input = get_embedding_input(text)
        return self.embedder.encode(f"{prefix}{normalized_input}").tolist()

    def embed_batch(self, texts: list[str], prefix: str = "passage: ") -> list[list[float]]:
        """Embed multiple texts after Romanized Nepali normalization.

        Args:
            texts: List of raw input texts.
            prefix: E5-family models require a task prefix.
                    Use "passage: " for document chunks (default),
                    "query: " for batch search queries.
        """
        normalized_inputs = [f"{prefix}{get_embedding_input(t)}" for t in texts]
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
            collection_name = self._ensure_business_collection(business_id)
            self.qdrant.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )

            logger.info(f"[RAG] Successfully stored {len(chunks)} Q&A chunks for doc {document_id} in Qdrant & DB")
            return len(chunks)

        except Exception as e:
            db.rollback()
            logger.error(f"[RAG] Document ingestion failed: {e}")
            raise e

    def retrieve_chunks(
        self,
        query_text: str,
        business_id: int,
        top_k: int = 5
    ) -> list[dict]:
        """Search Qdrant for top_k relevant chunks for a business."""
        try:
            if not self._collection_exists(business_id):
                logger.info("[RAG] No knowledge collection exists for business %s", business_id)
                return []
            collection_name = self.collection_name_for_business(business_id)
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
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                )
            else:
                response = self.qdrant.query_points(
                    collection_name=collection_name,
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
        platform: Optional[str] = None,
        customer_name: Optional[str] = None,
        business_name: Optional[str] = None,
        **kwargs
    ) -> Optional[dict]:
        """Full RAG pipeline: retrieve → generate → return answer with context memory."""
        start_time = time.time()
        resolved_business_name = (business_name or "").strip()

        try:
            detected_lang = language or self.detect_language(question)
            if not resolved_business_name and db:
                business = db.query(Business).filter(
                    Business.id == business_id
                ).first()
                resolved_business_name = (business.name or "").strip() if business else ""
            resolved_business_name = resolved_business_name or "Support Team"

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
                logger.info(
                    f"[RAG] Low confidence ({top_score:.3f}) or no chunks found. "
                    "Refusing cross-business/general policy assumptions."
                )
                context = (
                    "No sufficiently relevant business document was found. "
                    "Do not invent an answer or use another business's policies. "
                    "Tell the customer that the support team needs to confirm this information."
                )

            # 2. Build system prompt using unified prompt builder (Fix 4)
            system_prompt = build_system_prompt(
                context=context,
                mode=mode,
                language=detected_lang,
                sentiment=sentiment,
                platform=platform,
                customer_name=customer_name,
                business_name=resolved_business_name,
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
            import traceback
            logger.error(f"[RAG] Query failed:\n{traceback.format_exc()}")
            lang = language or "english"
            if not resolved_business_name and db:
                try:
                    business = db.query(Business).filter(
                        Business.id == business_id
                    ).first()
                    resolved_business_name = (
                        (business.name or "").strip() if business else ""
                    )
                except Exception:
                    resolved_business_name = ""
            resolved_business_name = resolved_business_name or "Support Team"
            fallback_answer = (
                f"Namaste! {resolved_business_name} support ma swagat cha. "
                "Ahile tapai ko request process garna samasya bhairako cha. "
                "Hamro team ko sadasya le chhittai follow up garnuhunecha."
                if lang == "romanized_nepali"
                else f"Hello! Welcome to {resolved_business_name} support. "
                "We're having trouble processing your request. "
                "A team member will follow up shortly."
            )
            return {
                "answer": fallback_answer,
                "confidence": 0.5,
                "sources": [],
                "chunks_used": 0,
                "language_detected": lang,
                "metadata": {"fallback_used": True, "error": str(e)}
            }

    def delete_document_chunks(self, document_id: int, business_id: int, db: Session):
        """Delete all chunks for a document from both Qdrant and PostgreSQL."""
        chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id,
            KnowledgeChunk.business_id == business_id,
        ).all()

        chunk_ids = [c.id for c in chunks]

        if chunk_ids and self._collection_exists(business_id):
            try:
                from qdrant_client.models import PointIdsList
                self.qdrant.delete(
                    collection_name=self.collection_name_for_business(business_id),
                    points_selector=PointIdsList(points=chunk_ids)
                )
                logger.info(f"[RAG] Deleted {len(chunk_ids)} points from Qdrant")
            except Exception as e:
                logger.error(f"[RAG] Failed to delete from Qdrant: {e}")

        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id,
            KnowledgeChunk.business_id == business_id,
        ).delete()
        db.commit()

    def update_chunk_embedding(
        self, chunk_id: int, new_content: str, business_id: int, db: Session
    ):
        """Re-embed and update a single chunk in Qdrant and update content in PostgreSQL."""
        chunk = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.id == chunk_id,
            KnowledgeChunk.business_id == business_id,
        ).first()
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        new_embedding = self.embed_text(new_content, prefix="passage: ")

        # Update PostgreSQL content
        chunk.content = new_content
        db.commit()

        # Update Qdrant (sole vector store)
        collection_name = self._ensure_business_collection(business_id)
        self.qdrant.upsert(
            collection_name=collection_name,
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
