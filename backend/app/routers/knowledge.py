import re
import hashlib
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, require_business_admin
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk, KnowledgeIngestionJob
from app.models.user import User
from app.services.rag_service import rag_service
from app.services.knowledge_ingestion import run_ingestion_job

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def knowledge_storage_path(
    business_id: int, document_id: int, safe_filename: str
) -> Path:
    """Derive a business-scoped path without accepting a caller path."""
    if business_id <= 0 or document_id <= 0:
        raise ValueError("Positive business and document IDs are required")
    root = Path(settings.KNOWLEDGE_UPLOAD_ROOT)
    return root / str(business_id) / f"{document_id}_{safe_filename}"


def run_ingestion_with_new_session(file_path, filename, document_id, business_id):
    # Backwards-compatible entry point for older callers. New uploads use the
    # durable job id and are processed by the shared worker.
    db = SessionLocal()
    try:
        job = db.query(KnowledgeIngestionJob).filter(
            KnowledgeIngestionJob.document_id == document_id,
            KnowledgeIngestionJob.business_id == business_id,
        ).order_by(KnowledgeIngestionJob.created_at.desc()).first()
        if not job:
            return False
        job_id = job.id
    finally:
        db.close()
    return run_ingestion_job(job_id)

# --- Upload document ---
@router.post('/upload')
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin),
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail='No business associated with this account')
    if not file.filename:
        raise HTTPException(status_code=400, detail='A filename is required.')

    allowed = {'pdf', 'docx', 'txt'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        raise HTTPException(status_code=400, detail='Unsupported file type. Allowed: PDF, DOCX, TXT')

    documents = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.business_id == business_id,
        KnowledgeDocument.source_type == 'upload',
    ).all()
    if len(documents) >= settings.KNOWLEDGE_MAX_DOCUMENTS:
        raise HTTPException(status_code=413, detail=f'Knowledge base limit reached ({settings.KNOWLEDGE_MAX_DOCUMENTS} documents).')

    def stored_size(document: KnowledgeDocument) -> int:
        if document.file_size:
            return document.file_size
        if document.storage_path:
            try:
                return Path(document.storage_path).stat().st_size
            except OSError:
                return 0
        return 0

    current_storage = sum(stored_size(document) for document in documents)
    safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file.filename)[:240] or f'document.{ext}'
    doc = None
    file_path = None
    total_size = 0
    digest = hashlib.sha256()
    try:
        # Create the row first so the business-scoped path has a stable id.
        doc = KnowledgeDocument(
            business_id=business_id,
            filename=safe_filename,
            status='processing',
            source_type='upload',
        )
        db.add(doc)
        db.flush()
        file_path = knowledge_storage_path(business_id, doc.id, safe_filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('wb') as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.KNOWLEDGE_MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail='File size exceeds the 10 MB limit.')
                output.write(chunk)
                digest.update(chunk)

        if total_size == 0:
            raise HTTPException(status_code=400, detail='File is empty.')
        if current_storage + total_size > settings.KNOWLEDGE_MAX_STORAGE_BYTES:
            raise HTTPException(status_code=413, detail='Business knowledge-base storage quota exceeded.')

        checksum = digest.hexdigest()
        duplicate = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.business_id == business_id,
            KnowledgeDocument.checksum == checksum,
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail='This document is already uploaded for the business.')

        doc.storage_path = file_path.as_posix()
        doc.file_size = total_size
        doc.checksum = checksum
        job = KnowledgeIngestionJob(
            document_id=doc.id,
            business_id=business_id,
            status='pending',
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    except HTTPException:
        db.rollback()
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail='Could not persist the uploaded document') from exc
    finally:
        await file.close()

    if background_tasks is not None:
        background_tasks.add_task(run_ingestion_job, job.id)
    return {
        'message': 'Document upload queued for indexing.',
        'document_id': doc.id,
        'filename': safe_filename,
        'status': 'processing',
        'job_id': job.id,
    }


# --- List documents ---
@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.business_id == business_id,
        KnowledgeDocument.source_type != 'agent_feedback',
    ).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.filename.rsplit(".", 1)[-1].lower() if "." in d.filename else "file",
            "file_size": d.file_size or 0,
            "status": d.status,
            "source_type": d.source_type,
            "processing_error": d.processing_error,
            "chunks": len(d.chunks),
            "created_at": d.uploaded_at.isoformat() if d.uploaded_at else "",
        }
        for d in docs
    ]


# --- Delete document ---
@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.business_id == business_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    rag_service.delete_document_chunks(document_id, business_id, db)
    if doc.storage_path:
        stored_file = Path(doc.storage_path)
        expected_parent = knowledge_storage_path(
            business_id, document_id, doc.filename
        ).parent.resolve()
        try:
            resolved_file = stored_file.resolve()
            if resolved_file.parent == expected_parent and resolved_file.exists():
                resolved_file.unlink()
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully."}


# --- Generate draft reply ---
class DraftRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []


@router.post("/generate-draft")
async def generate_draft(
    payload: DraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = await rag_service.query(
        question=payload.message,
        business_id=business_id,
        db=db
    )

    if not result:
        return {
            "draft": None,
            "language_detected": "english",
            "chunks_used": 0,
            "confidence": 0.0,
            "sources": [],
            "grounded": False,
            "source_details": []
        }

    return {
        "draft": result["answer"],
        "language_detected": result.get("language_detected", "english"),
        "chunks_used": result["chunks_used"],
        "confidence": result["confidence"],
        "sources": result["sources"],
        "grounded": result.get("grounded", False),
        "source_details": result.get("source_details", []),
    }


# --- Query knowledge base (For Testing in Frontend Settings) ---
@router.get("/config")
def get_knowledge_config(current_user: User = Depends(get_current_user)):
    return {
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dim": settings.EMBEDDING_DIM,
        "llm_model": settings.LLM_PRIMARY_MODEL
    }

class QueryRequest(BaseModel):
    question: str

@router.post("/query")
async def query_knowledge(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")

    result = await rag_service.query(
        question=payload.question,
        business_id=business_id,
        db=db
    )

    return result


class ChunkUpdateRequest(BaseModel):
    content: str


@router.get("/documents/{document_id}/chunks")
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")

    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.business_id == business_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == document_id
    ).order_by(KnowledgeChunk.page_number, KnowledgeChunk.id).all()

    return [
        {
            "id": c.id,
            "content": c.content,
            "page_number": c.page_number,
        }
        for c in chunks
    ]


@router.patch("/chunks/{chunk_id}")
def update_chunk(
    chunk_id: int,
    payload: ChunkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")

    chunk = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.id == chunk_id,
        KnowledgeChunk.business_id == business_id
    ).first()

    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    try:
        rag_service.update_chunk_embedding(
            chunk_id, payload.content, business_id, db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chunk: {e}")

    return {
        "id": chunk_id,
        "content": payload.content,
        "message": "Chunk updated and re-indexed in Qdrant"
    }

