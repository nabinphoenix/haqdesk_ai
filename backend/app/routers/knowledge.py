import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, require_business_admin
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.models.user import User
from app.services.rag_service import rag_service

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
    db = SessionLocal()
    try:
        rag_service.ingest_document(
            file_path=file_path,
            filename=filename,
            document_id=document_id,
            business_id=business_id,
            db=db
        )
    except Exception as e:
        print(f"Ingestion failed: {e}")
    finally:
        db.close()


# --- Upload document ---
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_admin)
):
    business_id = current_user.business_id
    if not business_id:
        raise HTTPException(status_code=403, detail="No business associated with this account")
    
    allowed = ["pdf", "docx", "txt"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    file_bytes = await file.read()
    
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")
    
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
        
    safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file.filename)

    doc = KnowledgeDocument(
        business_id=business_id,
        filename=safe_filename,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    file_path = knowledge_storage_path(business_id, doc.id, safe_filename)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_bytes)
        doc.storage_path = file_path.as_posix()
        db.commit()
    except Exception as exc:
        db.delete(doc)
        db.commit()
        raise HTTPException(
            status_code=500, detail="Could not persist the uploaded document"
        ) from exc

    background_tasks.add_task(
        run_ingestion_with_new_session,
        str(file_path),
        safe_filename,
        doc.id,
        business_id
    )

    return {
        "message": "Document upload started.",
        "document_id": doc.id,
        "filename": safe_filename,
        "status": "processing"
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
        KnowledgeDocument.business_id == business_id
    ).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.filename.rsplit(".", 1)[-1].lower() if "." in d.filename else "file",
            "file_size": sum(len(c.content.encode()) for c in d.chunks) if d.chunks else 0,
            "status": d.status,
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
            "sources": []
        }

    return {
        "draft": result["answer"],
        "language_detected": result.get("language_detected", "english"),
        "chunks_used": result["chunks_used"],
        "confidence": result["confidence"],
        "sources": result["sources"]
    }


# --- Query knowledge base (For Testing in Frontend Settings) ---
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

