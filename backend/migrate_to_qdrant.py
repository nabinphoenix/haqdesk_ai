import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.rag_service import rag_service
from app.services.qa_parser import parse_qa_pairs
from app.core.config import settings
from qdrant_client.models import PointStruct


def reindex_all_chunks():
    """
    Re-indexes database chunks into clean Q&A pairs, stores metadata in PostgreSQL,
    and upserts 1024-dim BAAI/bge-m3 embeddings into Qdrant.
    """
    db = SessionLocal()
    try:
        print("Starting Q&A Chunking & Qdrant Re-indexing...")

        chunks = db.query(KnowledgeChunk).all()
        print(f"Found {len(chunks)} total raw chunks in PostgreSQL.")

        if not chunks:
            print("No chunks found in database.")
            return

        full_text = "\n".join([c.content for c in chunks])
        qa_pairs = parse_qa_pairs(full_text)
        print(f"Extracted {len(qa_pairs)} clean Q&A pairs from existing document content.")

        business_id = chunks[0].business_id
        document_id = chunks[0].document_id

        # Clear existing un-parsed chunks in DB for business
        db.query(KnowledgeChunk).filter(KnowledgeChunk.business_id == business_id).delete()
        db.commit()

        # Re-populate KnowledgeChunk table with exact Q&A pairs
        db_chunks = []
        if qa_pairs:
            for qa in qa_pairs:
                kc = KnowledgeChunk(
                    business_id=business_id,
                    document_id=document_id,
                    content=qa["content"],
                    page_number=1
                )
                db.add(kc)
                db.flush()
                db_chunks.append(kc)
        else:
            for c in chunks:
                kc = KnowledgeChunk(
                    business_id=c.business_id,
                    document_id=c.document_id,
                    content=c.content,
                    page_number=c.page_number or 1
                )
                db.add(kc)
                db.flush()
                db_chunks.append(kc)

        db.commit()
        print(f"✅ Created {len(db_chunks)} Q&A KnowledgeChunk records in PostgreSQL.")

        # Batch embed and upsert to Qdrant
        chunk_texts = [c.content for c in db_chunks]
        embeddings = rag_service.embed_batch(chunk_texts)

        points = []
        for chunk, vector in zip(db_chunks, embeddings):
            points.append(
                PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload={
                        "business_id": chunk.business_id,
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "content": chunk.content,
                        "page_number": chunk.page_number or 1,
                        "filename": "TechSuru_RAG_AI_Knowledge_Base_FAQ.pdf",
                    }
                )
            )

        batch_size = 50
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            rag_service.qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=batch
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} ({len(batch)} points) to Qdrant")

        print(f"\n🎉 Successfully re-indexed {len(points)} Q&A pairs into Qdrant vector store!")

    except Exception as e:
        db.rollback()
        print(f"❌ Re-indexing failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reindex_all_chunks()
