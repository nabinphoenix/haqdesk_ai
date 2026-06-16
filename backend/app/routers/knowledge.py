from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import uuid
from jose import JWTError, jwt

from app.core.database import get_db, SessionLocal
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.rag_service import rag_service
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def get_business_id_from_token(token: Optional[str] = None, db: Session = Depends(get_db)) -> int:
    """Extract business_id from JWT token. Never trust frontend."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.business_id:
            raise HTTPException(status_code=403, detail="No business associated with this account")
        return user.business_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


def run_ingestion_with_new_session(tmp_path, filename, document_id, business_id):
    db = SessionLocal()
    try:
        rag_service.ingest_document(
            file_path=tmp_path,
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
    token: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    business_id = get_business_id_from_token(token, db)
    
    allowed = ["pdf", "docx", "txt"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    file_bytes = await file.read()

    doc = KnowledgeDocument(
        business_id=business_id,
        filename=file.filename,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(file_bytes)
    tmp.close()

    background_tasks.add_task(
        run_ingestion_with_new_session,
        tmp.name,
        file.filename,
        doc.id,
        business_id
    )

    return {
        "message": "Document upload started.",
        "document_id": doc.id,
        "filename": file.filename,
        "status": "processing"
    }


# --- List documents ---
@router.get("/documents")
def list_documents(
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    business_id = get_business_id_from_token(token, db)
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
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    business_id = get_business_id_from_token(token, db)
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.business_id == business_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    rag_service.delete_document_chunks(document_id, db)
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
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    business_id = get_business_id_from_token(token, db)
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = rag_service.query(
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
    token: Optional[str] = None


@router.post("/query")
async def query_knowledge(
    payload: QueryRequest,
    db: Session = Depends(get_db)
):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    business_id = get_business_id_from_token(payload.token, db)

    result = rag_service.query(
        question=payload.question,
        business_id=business_id,
        db=db
    )

    if not result:
        return {
            "answer": "No relevant knowledge found in the database for this question.",
            "confidence": 0.0,
            "sources": [],
            "chunks_used": 0
        }

    return result
