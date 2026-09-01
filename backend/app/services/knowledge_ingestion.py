import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeDocument, KnowledgeIngestionJob
from app.services.rag_service import rag_service

logger = logging.getLogger('uvicorn')
_claim_lock = threading.Lock()
_worker_started = False


def _now() -> datetime:
    return datetime.utcnow()


def _claim_job(job_id: int | None = None):
    with _claim_lock:
        db = SessionLocal()
        try:
            query = db.query(KnowledgeIngestionJob).filter(
                KnowledgeIngestionJob.status == 'pending',
                KnowledgeIngestionJob.available_at <= _now(),
            )
            if job_id is not None:
                query = query.filter(KnowledgeIngestionJob.id == job_id)
            # Prevent duplicate claims when multiple web workers share the queue.
            # SQLite ignores this clause; PostgreSQL uses row-level locking.
            if db.bind is not None and db.bind.dialect.name == 'postgresql':
                query = query.with_for_update(skip_locked=True)
            job = query.order_by(KnowledgeIngestionJob.created_at.asc()).first()
            if not job:
                return None
            job.status = 'processing'
            job.started_at = _now()
            job.attempts = (job.attempts or 0) + 1
            job.error = None
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == job.document_id,
                KnowledgeDocument.business_id == job.business_id,
            ).first()
            if not document:
                job.status = 'failed'
                job.error = 'Knowledge document no longer exists.'
                job.finished_at = _now()
                db.commit()
                return None
            document.status = 'processing'
            document.processing_error = None
            document.processing_started_at = _now()
            document.ingestion_attempts = job.attempts
            db.commit()
            return {
                'id': job.id,
                'document_id': job.document_id,
                'business_id': job.business_id,
                'attempts': job.attempts,
            }
        finally:
            db.close()


def run_ingestion_job(job_id: int | None = None) -> bool:
    claimed = _claim_job(job_id)
    if not claimed:
        return False

    db = SessionLocal()
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == claimed['document_id'],
            KnowledgeDocument.business_id == claimed['business_id'],
        ).first()
        job = db.query(KnowledgeIngestionJob).filter(
            KnowledgeIngestionJob.id == claimed['id'],
        ).first()
        if not document or not document.storage_path or not job:
            raise FileNotFoundError('Document storage record is missing.')
        file_path = Path(document.storage_path)
        if not file_path.is_file():
            raise FileNotFoundError(f'Uploaded document is missing: {file_path.name}')

        # Retry ingestion from a clean SQL/vector state after a partial failure.
        rag_service.delete_document_chunks(document.id, document.business_id, db)
        rag_service.ingest_document(
            file_path=str(file_path),
            filename=document.filename,
            document_id=document.id,
            business_id=document.business_id,
            db=db,
            source_type=document.source_type or 'upload',
        )
        document.status = 'ready'
        document.processing_error = None
        document.processed_at = _now()
        job.status = 'completed'
        job.finished_at = _now()
        db.commit()
        logger.info('[RAG] Ingestion job %s completed for document %s', job.id, document.id)
        return True
    except Exception as exc:
        db.rollback()
        logger.exception('[RAG] Ingestion job failed')
        job = db.query(KnowledgeIngestionJob).filter(
            KnowledgeIngestionJob.id == claimed['id'],
        ).first()
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == claimed['document_id'],
        ).first()
        attempts = claimed['attempts']
        max_attempts = max(1, settings.KNOWLEDGE_INGESTION_MAX_ATTEMPTS)
        terminal = attempts >= max_attempts
        if job:
            job.error = str(exc)[:4000]
            job.finished_at = _now() if terminal else None
            job.status = 'failed' if terminal else 'pending'
            if not terminal:
                job.available_at = _now() + timedelta(seconds=min(300, 2 ** attempts))
        if document:
            document.processing_error = str(exc)[:4000]
            document.status = 'failed' if terminal else 'processing'
        db.commit()
        return False
    finally:
        db.close()


def recover_stale_jobs() -> int:
    db = SessionLocal()
    try:
        cutoff = _now() - timedelta(seconds=max(60, settings.KNOWLEDGE_INGESTION_STALE_SECONDS))
        stale = db.query(KnowledgeIngestionJob).filter(
            KnowledgeIngestionJob.status == 'processing',
            KnowledgeIngestionJob.started_at < cutoff,
        ).all()
        for job in stale:
            job.status = 'pending'
            job.available_at = _now()
            job.error = 'Recovered after an interrupted ingestion worker.'
            document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == job.document_id).first()
            if document:
                document.status = 'processing'
                document.processing_error = job.error
        db.commit()
        return len(stale)
    finally:
        db.close()


def _worker_loop() -> None:
    recover_stale_jobs()
    while True:
        try:
            run_ingestion_job()
        except Exception:
            logger.exception('[RAG] Ingestion worker loop failed')
        time.sleep(max(0.5, settings.KNOWLEDGE_INGESTION_POLL_SECONDS))


def start_knowledge_ingestion_worker() -> None:
    global _worker_started
    if _worker_started or not settings.KNOWLEDGE_INGESTION_WORKER_ENABLED:
        return
    _worker_started = True
    thread = threading.Thread(target=_worker_loop, name='knowledge-ingestion-worker', daemon=True)
    thread.start()
    logger.info('[RAG] Durable knowledge ingestion worker started')
