from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.core.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    business_id = current_user.business_id
    if not business_id:
        return {}

    # Total messages
    total_messages = db.query(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(Conversation.business_id == business_id).count()

    # Customer messages
    customer_messages = db.query(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.business_id == business_id,
        Message.sender_type == "customer"
    ).count()

    # Agent messages
    agent_messages = db.query(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.business_id == business_id,
        Message.sender_type == "agent"
    ).count()

    # AI drafts generated
    ai_drafts = db.query(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.business_id == business_id,
        Message.ai_draft.isnot(None)
    ).count()

    # Total conversations
    total_conversations = db.query(Conversation).filter(
        Conversation.business_id == business_id
    ).count()

    # Open conversations
    open_conversations = db.query(Conversation).filter(
        Conversation.business_id == business_id,
        Conversation.status == "open"
    ).count()

    # Total customers
    total_customers = db.query(Customer).filter(
        Customer.business_id == business_id
    ).count()

    # Platform breakdown
    platform_counts = db.query(
        Customer.platform,
        func.count(Conversation.id).label("count")
    ).join(
        Conversation, Conversation.customer_id == Customer.id
    ).filter(
        Conversation.business_id == business_id
    ).group_by(Customer.platform).all()

    platform_data = {row.platform: row.count for row in platform_counts}

    # Sentiment breakdown
    sentiment_counts = db.query(
        Message.sentiment,
        func.count(Message.id).label("count")
    ).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.business_id == business_id,
        Message.sentiment.isnot(None)
    ).group_by(Message.sentiment).all()

    sentiment_data = {row.sentiment: row.count for row in sentiment_counts}

    # Messages per day last 7 days
    messages_per_day = db.execute(text("""
        SELECT DATE(m.timestamp) as day, COUNT(*) as count
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.business_id = :biz_id
        AND m.timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(m.timestamp)
        ORDER BY day ASC
    """), {"biz_id": business_id}).fetchall()

    daily_data = [{"date": str(row.day), "count": row.count} for row in messages_per_day]

    # Knowledge base stats
    kb_docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.business_id == business_id
    ).count()
    kb_chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.business_id == business_id
    ).count()

    # Team members
    team_count = db.query(User).filter(User.business_id == business_id).count()

    return {
        "total_messages": total_messages,
        "customer_messages": customer_messages,
        "agent_messages": agent_messages,
        "ai_drafts_generated": ai_drafts,
        "total_conversations": total_conversations,
        "open_conversations": open_conversations,
        "total_customers": total_customers,
        "team_members": team_count,
        "platform_breakdown": platform_data,
        "sentiment_breakdown": sentiment_data,
        "messages_per_day": daily_data,
        "knowledge_documents": kb_docs,
        "knowledge_chunks": kb_chunks,
    }
