import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models.knowledge import AgentReplyFeedback, KnowledgeChunk, KnowledgeDocument
from app.services.rag_service import rag_service

logger = logging.getLogger('uvicorn')


def index_approved_feedback(feedback_id: int) -> bool:
    '''Index an agent-approved answer as a tenant-scoped example.'''
    db = SessionLocal()
    point_id = None
    collection_name = None
    try:
        feedback = db.query(AgentReplyFeedback).filter(AgentReplyFeedback.id == feedback_id).first()
        if not feedback or feedback.indexed:
            return False

        document = KnowledgeDocument(
            business_id=feedback.business_id,
            filename=f'approved-agent-reply-{feedback.id}.txt',
            status='processing',
            source_type='agent_feedback',
        )
        db.add(document)
        db.flush()
        feedback.knowledge_document_id = document.id
        content = (
            'Approved agent example. Use this as a style and resolution example, '
            'not as a business policy unless supported by an uploaded policy document.\n\n'
            f'Customer question: {feedback.question[:4000]}\n'
            f'Approved answer: {feedback.approved_answer[:4000]}'
        )
        chunk = KnowledgeChunk(
            business_id=feedback.business_id,
            document_id=document.id,
            content=content,
            page_number=1,
        )
        db.add(chunk)
        db.flush()
        vector = rag_service.embed_text(content, prefix='passage: ')
        collection_name = rag_service._ensure_business_collection(feedback.business_id)
        point_id = chunk.id
        from qdrant_client.models import PointStruct
        rag_service.qdrant.upsert(
            collection_name=collection_name,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    'business_id': feedback.business_id,
                    'document_id': document.id,
                    'chunk_id': chunk.id,
                    'content': content,
                    'page_number': 1,
                    'filename': document.filename,
                    'source_type': 'agent_feedback',
                },
            )],
        )
        document.status = 'ready'
        document.processed_at = datetime.utcnow()
        feedback.indexed = True
        db.commit()
        logger.info('[RAG] Indexed approved agent feedback %s', feedback_id)
        return True
    except Exception:
        db.rollback()
        if point_id and collection_name:
            try:
                from qdrant_client.models import PointIdsList
                rag_service.qdrant.delete(
                    collection_name=collection_name,
                    points_selector=PointIdsList(points=[point_id]),
                )
            except Exception:
                logger.exception('[RAG] Could not clean up feedback vector')
        logger.exception('[RAG] Failed to index approved agent feedback %s', feedback_id)
        return False
    finally:
        db.close()