"""Discover recurring customer questions and turn reviewed opportunities into knowledge drafts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import math
import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.faq_opportunity import FAQOpportunityFeedback
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.message import Message
from app.schemas.analytics import AnalyticsFilters
from app.services.rag_service import rag_service


MAX_MESSAGES_TO_ANALYSE = 500
SEMANTIC_SIMILARITY_THRESHOLD = 0.82
TEXT_SIMILARITY_THRESHOLD = 0.60
MAX_EXAMPLES_PER_TOPIC = 3

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.IGNORECASE)
_URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)")
_ORDER_RE = re.compile(r"(?<!\w)(?:order\s*(?:no|number|#)?\s*[:#-]?\s*|#)\d{4,}\b", re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[\w\u0900-\u097f]+", re.UNICODE)

QUESTION_STARTERS = {
    "what", "when", "where", "why", "who", "how", "can", "could", "would", "will", "do", "does", "did",
    "is", "are", "am", "price", "cost", "delivery", "shipping", "track", "tracking", "payment", "refund",
    "return", "exchange", "available", "availability", "size", "order", "discount", "offer", "kati", "kasari",
    "kahile", "kina", "cha", "chha", "hunchha", "huncha", "delivery", "price", "payment", "order",
}
QUESTION_TERMS = {
    "price", "cost", "delivery", "shipping", "track", "tracking", "payment", "refund", "return", "exchange",
    "available", "availability", "size", "order", "discount", "offer", "kati", "kasari", "kahile", "kina",
    "delivery", "paisa", "bhuktani", "pathaunu", "stock",
}


@dataclass
class QuestionCandidate:
    message_id: int
    customer_id: int | None
    platform: str
    asked_at: datetime | None
    display_text: str
    normalized_text: str


@dataclass
class QuestionCluster:
    candidates: list[QuestionCandidate] = field(default_factory=list)
    vectors: list[list[float]] = field(default_factory=list)
    centroid: list[float] | None = None

    def add(self, candidate: QuestionCandidate, vector: list[float] | None) -> None:
        self.candidates.append(candidate)
        if vector is not None:
            self.vectors.append(vector)
            self.centroid = _average_vector(self.vectors)


def _mask_sensitive_text(text: str) -> str:
    """Keep examples useful while masking common direct identifiers before analysis or display."""
    masked = _EMAIL_RE.sub("[email]", text)
    masked = _URL_RE.sub("[link]", masked)
    masked = _ORDER_RE.sub("[order number]", masked)
    masked = _PHONE_RE.sub("[phone]", masked)
    return _SPACE_RE.sub(" ", masked).strip()


def _normalize_question(text: str) -> str:
    value = text.lower().strip()
    value = re.sub(r"[^\w\s\u0900-\u097f]", " ", value, flags=re.UNICODE)
    return _SPACE_RE.sub(" ", value).strip()


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(_normalize_question(text)))


def _looks_like_question(text: str) -> bool:
    normalized = _normalize_question(text)
    if len(normalized) < 8:
        return False
    tokens = _tokens(normalized)
    if not tokens:
        return False
    starts_with_signal = any(normalized.startswith(f"{starter} ") or normalized == starter for starter in QUESTION_STARTERS)
    has_question_mark = "?" in text or "؟" in text
    has_question_term = bool(tokens & QUESTION_TERMS)
    return has_question_mark or starts_with_signal or has_question_term


def _cosine(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if not left_values or len(left_values) != len(right_values):
        return 0.0
    dot = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = math.sqrt(sum(a * a for a in left_values))
    right_norm = math.sqrt(sum(b * b for b in right_values))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _text_similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _average_vector(vectors: list[list[float]]) -> list[float] | None:
    if not vectors:
        return None
    length = len(vectors[0])
    if not length or any(len(vector) != length for vector in vectors):
        return None
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(length)]


def _topic_title(candidate: QuestionCandidate) -> str:
    text = candidate.display_text.strip().rstrip("?!. ")
    if len(text) > 110:
        text = f"{text[:107].rstrip()}..."
    return f"FAQ: {text}" if text else "FAQ opportunity"


def _filename_for_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70] or "faq-opportunity"
    return f"{slug}.txt"


class FAQOpportunityService:
    """Runs bounded, tenant-scoped semantic clustering over customer question messages."""

    def __init__(self, db: Session):
        self.db = db

    def discover(
        self,
        business_id: int,
        filters: AnalyticsFilters,
        min_occurrences: int = 5,
        min_unique_customers: int = 3,
        include_dismissed: bool = False,
    ) -> dict:
        candidates, scanned = self._load_question_candidates(business_id, filters)
        clusters, method = self._cluster(candidates)
        feedback = {
            row.fingerprint: row
            for row in self.db.query(FAQOpportunityFeedback).filter(
                FAQOpportunityFeedback.business_id == business_id
            ).all()
        }
        opportunities = []
        for cluster in clusters:
            unique_customers = {candidate.customer_id for candidate in cluster.candidates if candidate.customer_id is not None}
            if len(cluster.candidates) < min_occurrences or len(unique_customers) < min_unique_customers:
                continue
            opportunity = self._serialize_cluster(cluster, feedback)
            if opportunity["status"] == "dismissed" and not include_dismissed:
                continue
            opportunities.append(opportunity)
        opportunities.sort(key=lambda item: (-item["occurrence_count"], -item["unique_customer_count"], item["suggested_title"]))
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_method": method,
            "messages_scanned": scanned,
            "question_candidates": len(candidates),
            "minimum_occurrences": min_occurrences,
            "minimum_unique_customers": min_unique_customers,
            "opportunities": opportunities,
            "privacy_note": "Examples mask common emails, phone numbers, links, and order numbers before analysis and display.",
        }

    def dismiss(self, business_id: int, fingerprint: str) -> dict:
        feedback = self._feedback(business_id, fingerprint)
        feedback.status = "dismissed"
        self.db.add(feedback)
        self.db.commit()
        return {"fingerprint": fingerprint, "status": feedback.status}

    def create_knowledge_draft(
        self,
        business_id: int,
        fingerprint: str,
        title: str,
        representative_question: str,
        example_questions: list[str],
    ) -> dict:
        feedback = self._feedback(business_id, fingerprint)
        if feedback.knowledge_document_id:
            existing = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == feedback.knowledge_document_id,
                KnowledgeDocument.business_id == business_id,
            ).first()
            if existing:
                return {
                    "knowledge_document_id": existing.id,
                    "filename": existing.filename,
                    "status": feedback.status,
                    "message": "A Knowledge Base draft already exists for this FAQ opportunity.",
                }

        safe_title = _mask_sensitive_text(title).strip()[:160] or "FAQ opportunity"
        safe_question = _mask_sensitive_text(representative_question).strip()[:800]
        safe_examples = [
            _mask_sensitive_text(question).strip()[:500]
            for question in example_questions[:MAX_EXAMPLES_PER_TOPIC]
            if _mask_sensitive_text(question).strip()
        ]
        if not safe_question:
            raise ValueError("A representative question is required")

        document = KnowledgeDocument(
            business_id=business_id,
            filename=_filename_for_title(safe_title),
            status="draft",
        )
        self.db.add(document)
        self.db.flush()
        examples = "\n".join(f"- {question}" for question in safe_examples) or f"- {safe_question}"
        content = (
            f"FAQ draft - Administrator review required\n\n"
            f"Suggested title: {safe_title}\n\n"
            f"Customer question: {safe_question}\n\n"
            f"Representative customer wording:\n{examples}\n\n"
            "Approved answer:\n"
            "[Write an accurate, business-approved answer here before saving and indexing this draft.]"
        )
        self.db.add(KnowledgeChunk(
            business_id=business_id,
            document_id=document.id,
            content=content,
            page_number=1,
        ))
        feedback.status = "draft_created"
        feedback.knowledge_document_id = document.id
        self.db.add(feedback)
        self.db.commit()
        return {
            "knowledge_document_id": document.id,
            "filename": document.filename,
            "status": feedback.status,
            "message": "Knowledge Base draft created. Review and save it before it is indexed for AI replies.",
        }

    def _load_question_candidates(self, business_id: int, filters: AnalyticsFilters) -> tuple[list[QuestionCandidate], int]:
        query = self.db.query(Message, Conversation).join(
            Conversation, Message.conversation_id == Conversation.id
        ).filter(
            Conversation.business_id == business_id,
            Message.sender_type == "customer",
            Message.content.isnot(None),
            Message.timestamp >= filters.from_,
            Message.timestamp < filters.to,
        )
        if not filters.include_deleted:
            query = query.filter(Conversation.is_deleted.is_(False))
        if filters.platform is not None:
            query = query.filter(Message.platform == filters.platform.value)
        if filters.agent_id is not None:
            query = query.filter(Conversation.assigned_agent_id == filters.agent_id)
        if filters.status is not None:
            query = query.filter(Conversation.status == filters.status.value)
        if filters.priority is not None:
            query = query.filter(Conversation.priority == filters.priority.value)

        rows = query.order_by(Message.timestamp.desc(), Message.id.desc()).limit(MAX_MESSAGES_TO_ANALYSE).all()
        candidates = []
        for message, conversation in rows:
            display_text = _mask_sensitive_text(message.content or "")
            if not _looks_like_question(display_text):
                continue
            normalized = _normalize_question(display_text)
            if normalized:
                candidates.append(QuestionCandidate(
                    message_id=message.id,
                    customer_id=conversation.customer_id,
                    platform=(message.platform or "other").lower(),
                    asked_at=message.timestamp,
                    display_text=display_text[:800],
                    normalized_text=normalized[:800],
                ))
        return candidates, len(rows)

    def _cluster(self, candidates: list[QuestionCandidate]) -> tuple[list[QuestionCluster], str]:
        if not candidates:
            return [], "semantic_embeddings"
        vectors: list[list[float] | None]
        method = "semantic_embeddings"
        try:
            embedded = rag_service.embed_batch([candidate.display_text for candidate in candidates], prefix="query: ")
            vectors = [list(vector) for vector in embedded]
            if len(vectors) != len(candidates):
                raise ValueError("Embedding output count did not match question count")
        except Exception:
            vectors = [None] * len(candidates)
            method = "text_similarity_fallback"

        clusters: list[QuestionCluster] = []
        for candidate, vector in zip(candidates, vectors):
            best_cluster: QuestionCluster | None = None
            best_score = -1.0
            for cluster in clusters:
                if vector is not None and cluster.centroid is not None:
                    score = _cosine(vector, cluster.centroid)
                    threshold = SEMANTIC_SIMILARITY_THRESHOLD
                else:
                    score = _text_similarity(candidate.normalized_text, cluster.candidates[0].normalized_text)
                    threshold = TEXT_SIMILARITY_THRESHOLD
                if score >= threshold and score > best_score:
                    best_score = score
                    best_cluster = cluster
            if best_cluster is None:
                best_cluster = QuestionCluster()
                clusters.append(best_cluster)
            best_cluster.add(candidate, vector)
        return clusters, method

    def _serialize_cluster(self, cluster: QuestionCluster, feedback: dict[str, FAQOpportunityFeedback]) -> dict:
        normalized_counts = Counter(candidate.normalized_text for candidate in cluster.candidates)
        representative_normalized = normalized_counts.most_common(1)[0][0]
        representative = next(candidate for candidate in cluster.candidates if candidate.normalized_text == representative_normalized)
        fingerprint = sha256(representative_normalized.encode("utf-8")).hexdigest()
        platforms = Counter(candidate.platform for candidate in cluster.candidates)
        customer_ids = {candidate.customer_id for candidate in cluster.candidates if candidate.customer_id is not None}
        examples: list[str] = []
        seen = set()
        for candidate in cluster.candidates:
            if candidate.normalized_text not in seen:
                seen.add(candidate.normalized_text)
                examples.append(candidate.display_text)
            if len(examples) >= MAX_EXAMPLES_PER_TOPIC:
                break
        state = feedback.get(fingerprint)
        last_asked_at = max((candidate.asked_at for candidate in cluster.candidates if candidate.asked_at), default=None)
        return {
            "fingerprint": fingerprint,
            "suggested_title": _topic_title(representative),
            "representative_question": representative.display_text,
            "example_questions": examples,
            "occurrence_count": len(cluster.candidates),
            "unique_customer_count": len(customer_ids),
            "channels": dict(sorted(platforms.items())),
            "last_asked_at": last_asked_at.isoformat() if last_asked_at else None,
            "status": state.status if state else "active",
            "knowledge_document_id": state.knowledge_document_id if state else None,
        }

    def _feedback(self, business_id: int, fingerprint: str) -> FAQOpportunityFeedback:
        if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
            raise ValueError("Invalid FAQ opportunity fingerprint")
        feedback = self.db.query(FAQOpportunityFeedback).filter(
            FAQOpportunityFeedback.business_id == business_id,
            FAQOpportunityFeedback.fingerprint == fingerprint,
        ).first()
        if feedback is None:
            feedback = FAQOpportunityFeedback(
                business_id=business_id,
                fingerprint=fingerprint,
                status="active",
            )
        return feedback