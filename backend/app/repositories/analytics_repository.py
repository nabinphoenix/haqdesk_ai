from datetime import datetime, timezone

from sqlalchemy import and_, case, func, text
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.message import Message
from app.models.integration import Integration
from app.models.user import User
from app.schemas.analytics import AnalyticsFilters


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _conversation_conditions(
        business_id: int,
        filters: AnalyticsFilters,
        start: datetime,
        end: datetime,
        include_dates: bool = True,
    ):
        conditions = [Conversation.business_id == business_id]
        if include_dates:
            conditions.extend([Conversation.created_at >= start, Conversation.created_at < end])
        if not filters.include_deleted:
            conditions.append(Conversation.is_deleted.is_(False))
        if filters.agent_id is not None:
            conditions.append(Conversation.assigned_agent_id == filters.agent_id)
        if filters.status is not None:
            conditions.append(Conversation.status == filters.status.value)
        if filters.priority is not None:
            conditions.append(Conversation.priority == filters.priority.value)
        if filters.platform is not None:
            conditions.append(Customer.platform == filters.platform.value)
        return conditions

    def conversation_counts(self, business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        query = self.db.query(
            func.count(Conversation.id).label("total"),
            func.count(case((Conversation.status == "open", 1))).label("open"),
            func.count(case((Conversation.status == "pending", 1))).label("pending"),
            func.count(case((Conversation.status == "resolved", 1))).label("resolved"),
            func.count(func.distinct(Conversation.customer_id)).label("customers"),
        ).join(Customer, Customer.id == Conversation.customer_id)
        return query.filter(*self._conversation_conditions(business_id, filters, start, end)).one()

    def message_counts(self, business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        conditions = self._conversation_conditions(
            business_id, filters, start, end, include_dates=False
        ) + [Message.timestamp >= start, Message.timestamp < end]
        return self.db.query(
            func.count(Message.id).label("total"),
            func.count(case((Message.sender_type == "customer", 1))).label("customer"),
            func.count(case((Message.sender_type == "agent", 1))).label("agent"),
            func.count(case((Message.ai_draft.isnot(None), 1))).label("drafts"),
        ).join(Conversation, Conversation.id == Message.conversation_id).join(
            Customer, Customer.id == Conversation.customer_id
        ).filter(*conditions).one()

    def knowledge_counts(self, business_id: int, start: datetime, end: datetime):
        documents = self.db.query(func.count(KnowledgeDocument.id)).filter(
            KnowledgeDocument.business_id == business_id,
            KnowledgeDocument.uploaded_at >= start,
            KnowledgeDocument.uploaded_at < end,
        ).scalar() or 0
        chunks = self.db.query(func.count(KnowledgeChunk.id)).join(
            KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id
        ).filter(
            KnowledgeDocument.business_id == business_id,
            KnowledgeDocument.uploaded_at >= start,
            KnowledgeDocument.uploaded_at < end,
        ).scalar() or 0
        return documents, chunks

    def team_count(self, business_id: int) -> int:
        return self.db.query(func.count(User.id)).filter(User.business_id == business_id).scalar() or 0

    def platform_distribution(self, business_id: int, filters: AnalyticsFilters):
        conditions = self._conversation_conditions(
            business_id, filters, filters.from_, filters.to
        )
        rows = self.db.query(
            Customer.platform, func.count(Conversation.id)
        ).join(Conversation, Conversation.customer_id == Customer.id).filter(
            *conditions
        ).group_by(Customer.platform).all()
        return {str(platform or "unknown"): count for platform, count in rows}

    def sentiment_distribution(self, business_id: int, filters: AnalyticsFilters):
        conditions = self._conversation_conditions(
            business_id, filters, filters.from_, filters.to, include_dates=False
        ) + [
            Message.timestamp >= filters.from_, Message.timestamp < filters.to,
            Message.sentiment.isnot(None),
        ]
        rows = self.db.query(Message.sentiment, func.count(Message.id)).join(
            Conversation, Conversation.id == Message.conversation_id
        ).join(Customer, Customer.id == Conversation.customer_id).filter(
            *conditions
        ).group_by(Message.sentiment).all()
        return {str(sentiment): count for sentiment, count in rows}

    def message_trend(self, business_id: int, filters: AnalyticsFilters, bucket: str):
        interval = {"hour": "1 hour", "day": "1 day", "week": "1 week", "month": "1 month"}[bucket]
        clauses = [
            "c.business_id = :business_id",
            "m.timestamp >= :from_utc",
            "m.timestamp < :to_utc",
        ]
        params = {
            "business_id": business_id,
            "from_utc": filters.from_,
            "to_utc": filters.to,
            "timezone": filters.timezone,
        }
        if not filters.include_deleted:
            clauses.append("c.is_deleted = FALSE")
        if filters.platform is not None:
            clauses.append("cu.platform = :platform")
            params["platform"] = filters.platform.value
        if filters.agent_id is not None:
            clauses.append("c.assigned_agent_id = :agent_id")
            params["agent_id"] = filters.agent_id
        if filters.status is not None:
            clauses.append("c.status = :status")
            params["status"] = filters.status.value
        if filters.priority is not None:
            clauses.append("c.priority = :priority")
            params["priority"] = filters.priority.value

        sql = text(f"""
            WITH bounds AS (
                SELECT
                    date_trunc('{bucket}', timezone(:timezone, CAST(:from_utc AS TIMESTAMPTZ))) AS first_bucket,
                    date_trunc('{bucket}', timezone(:timezone, CAST(:to_utc AS TIMESTAMPTZ) - INTERVAL '1 microsecond')) AS last_bucket
            ), buckets AS (
                SELECT generate_series(first_bucket, last_bucket, INTERVAL '{interval}') AS bucket_start
                FROM bounds
            ), counts AS (
                SELECT
                    date_trunc('{bucket}', timezone(:timezone, m.timestamp)) AS bucket_start,
                    COUNT(*) AS all_messages,
                    COUNT(*) FILTER (WHERE m.sender_type = 'customer') AS customer_messages,
                    COUNT(*) FILTER (WHERE m.sender_type = 'agent') AS agent_messages
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN customers cu ON cu.id = c.customer_id
                WHERE {' AND '.join(clauses)}
                GROUP BY 1
            )
            SELECT b.bucket_start,
                   COALESCE(c.all_messages, 0) AS all_messages,
                   COALESCE(c.customer_messages, 0) AS customer_messages,
                   COALESCE(c.agent_messages, 0) AS agent_messages
            FROM buckets b
            LEFT JOIN counts c ON c.bucket_start = b.bucket_start
            ORDER BY b.bucket_start
        """)
        return self.db.execute(sql, params).mappings().all()

    @staticmethod
    def _platform_sql_parts(filters: AnalyticsFilters, *, alias="c", customer_alias="cu"):
        clauses = [f"{alias}.business_id = :business_id"]
        if not filters.include_deleted:
            clauses.append(f"{alias}.is_deleted = FALSE")
        if filters.agent_id is not None:
            clauses.append(f"{alias}.assigned_agent_id = :agent_id")
        if filters.status is not None:
            clauses.append(f"{alias}.status = :status")
        if filters.priority is not None:
            clauses.append(f"{alias}.priority = :priority")
        if filters.platform is not None:
            clauses.append(f"LOWER({customer_alias}.platform) = :platform")
        return clauses

    @staticmethod
    def _platform_params(business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        return {
            "business_id": business_id, "from_utc": start, "to_utc": end,
            "timezone": filters.timezone,
            "agent_id": filters.agent_id,
            "status": filters.status.value if filters.status else None,
            "priority": filters.priority.value if filters.priority else None,
            "platform": filters.platform.value if filters.platform else None,
        }

    def platform_period_stats(self, business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        clauses = self._platform_sql_parts(filters)
        where = " AND ".join(clauses)
        sql = text(f"""
            WITH conversation_stats AS (
                SELECT LOWER(cu.platform) AS platform,
                       COUNT(*) AS conversations
                FROM conversations c JOIN customers cu ON cu.id = c.customer_id
                WHERE {where} AND c.created_at >= :from_utc AND c.created_at < :to_utc
                GROUP BY 1
            ), message_stats AS (
                SELECT LOWER(COALESCE(m.platform, cu.platform)) AS platform,
                       COUNT(*) AS messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'customer') AS inbound_messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'agent') AS outgoing_messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'customer' AND LOWER(m.sentiment) = 'positive') AS positive_messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'customer' AND LOWER(m.sentiment) = 'neutral') AS neutral_messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'customer' AND LOWER(m.sentiment) = 'negative') AS negative_messages,
                       COUNT(*) FILTER (WHERE LOWER(m.sender_type) = 'customer' AND (m.sentiment IS NULL OR LOWER(m.sentiment) NOT IN ('positive','neutral','negative'))) AS unclassified_messages
                FROM messages m JOIN conversations c ON c.id = m.conversation_id
                JOIN customers cu ON cu.id = c.customer_id
                WHERE {where} AND m.timestamp >= :from_utc AND m.timestamp < :to_utc
                GROUP BY 1
            ), activity_customers AS (
                SELECT LOWER(cu.platform) AS platform,
                       COALESCE(ci.master_customer_id, cu.merged_into_id, cu.id) AS canonical_id
                FROM conversations c JOIN customers cu ON cu.id = c.customer_id
                LEFT JOIN customer_identities ci ON ci.linked_customer_id = cu.id AND ci.business_id = :business_id
                WHERE {where} AND c.created_at >= :from_utc AND c.created_at < :to_utc
                UNION
                SELECT LOWER(COALESCE(m.platform, cu.platform)),
                       COALESCE(ci.master_customer_id, cu.merged_into_id, cu.id)
                FROM messages m JOIN conversations c ON c.id = m.conversation_id
                JOIN customers cu ON cu.id = c.customer_id
                LEFT JOIN customer_identities ci ON ci.linked_customer_id = cu.id AND ci.business_id = :business_id
                WHERE {where} AND m.timestamp >= :from_utc AND m.timestamp < :to_utc
            ), customer_stats AS (
                SELECT platform, COUNT(DISTINCT canonical_id) AS unique_customers
                FROM activity_customers GROUP BY platform
            )
            SELECT COALESCE(cs.platform, ms.platform, us.platform) AS platform,
                   COALESCE(cs.conversations, 0) AS conversations,
                   COALESCE(ms.messages, 0) AS messages,
                   COALESCE(ms.inbound_messages, 0) AS inbound_messages,
                   COALESCE(ms.outgoing_messages, 0) AS outgoing_messages,
                   COALESCE(ms.positive_messages, 0) AS positive_messages,
                   COALESCE(ms.neutral_messages, 0) AS neutral_messages,
                   COALESCE(ms.negative_messages, 0) AS negative_messages,
                   COALESCE(ms.unclassified_messages, 0) AS unclassified_messages,
                   COALESCE(us.unique_customers, 0) AS unique_customers
            FROM conversation_stats cs FULL JOIN message_stats ms ON ms.platform = cs.platform
            FULL JOIN customer_stats us ON us.platform = COALESCE(cs.platform, ms.platform)
        """)
        return self.db.execute(sql, self._platform_params(business_id, filters, start, end)).mappings().all()

    def platform_backlog(self, business_id: int, filters: AnalyticsFilters):
        where = " AND ".join(self._platform_sql_parts(filters))
        sql = text(f"""
            SELECT LOWER(cu.platform) AS platform,
                   COUNT(*) FILTER (WHERE c.status = 'open') AS open,
                   COUNT(*) FILTER (WHERE c.status = 'pending') AS pending,
                   COUNT(*) FILTER (WHERE c.status = 'resolved') AS resolved,
                   COUNT(*) FILTER (WHERE c.assigned_agent_id IS NULL) AS unassigned,
                   COUNT(*) FILTER (WHERE c.priority = 'high') AS high_priority,
                   COUNT(*) FILTER (WHERE c.priority = 'urgent') AS urgent_priority
            FROM conversations c JOIN customers cu ON cu.id = c.customer_id
            WHERE {where} GROUP BY 1
        """)
        return self.db.execute(sql, self._platform_params(business_id, filters, filters.from_, filters.to)).mappings().all()

    def platform_response_times(self, business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        where = " AND ".join(self._platform_sql_parts(filters))
        sql = text(f"""
            WITH first_inbound AS (
                SELECT c.id AS conversation_id, LOWER(COALESCE(m.platform, cu.platform)) AS platform,
                       MIN(m.timestamp) AS first_customer_at
                FROM messages m JOIN conversations c ON c.id = m.conversation_id
                JOIN customers cu ON cu.id = c.customer_id
                WHERE {where} AND LOWER(m.sender_type) = 'customer'
                  AND m.timestamp >= :from_utc AND m.timestamp < :to_utc
                GROUP BY c.id, LOWER(COALESCE(m.platform, cu.platform))
            ), response AS (
                SELECT fi.*, MIN(m.timestamp) AS first_agent_at
                FROM first_inbound fi LEFT JOIN messages m
                  ON m.conversation_id = fi.conversation_id
                 AND LOWER(m.sender_type) = 'agent'
                 AND m.timestamp > fi.first_customer_at AND m.timestamp < :to_utc
                GROUP BY fi.conversation_id, fi.platform, fi.first_customer_at
            ), durations AS (
                SELECT platform, EXTRACT(EPOCH FROM (first_agent_at - first_customer_at)) AS seconds,
                       first_agent_at IS NULL AS unanswered FROM response
            )
            SELECT platform, AVG(seconds) AS average_seconds,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY seconds) AS median_seconds,
                   percentile_cont(0.9) WITHIN GROUP (ORDER BY seconds) AS p90_seconds,
                   COUNT(seconds) AS sample_size,
                   COUNT(*) FILTER (WHERE unanswered) AS unanswered
            FROM durations GROUP BY platform
        """)
        return self.db.execute(sql, self._platform_params(business_id, filters, start, end)).mappings().all()

    def platform_peaks(self, business_id: int, filters: AnalyticsFilters):
        where = " AND ".join(self._platform_sql_parts(filters))
        sql = text(f"""
            WITH message_slots AS (
                SELECT LOWER(COALESCE(m.platform, cu.platform)) AS platform,
                       EXTRACT(ISODOW FROM timezone(:timezone, m.timestamp))::int AS weekday,
                       EXTRACT(HOUR FROM timezone(:timezone, m.timestamp))::int AS hour,
                       COUNT(*) AS message_count
                FROM messages m JOIN conversations c ON c.id=m.conversation_id
                JOIN customers cu ON cu.id=c.customer_id
                WHERE {where} AND m.timestamp >= :from_utc AND m.timestamp < :to_utc
                GROUP BY 1,2,3
            ), ranked_messages AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY platform ORDER BY message_count DESC, weekday, hour) AS rn
                FROM message_slots
            ), conversation_slots AS (
                SELECT LOWER(cu.platform) AS platform,
                       EXTRACT(HOUR FROM timezone(:timezone, c.created_at))::int AS hour,
                       COUNT(*) AS conversation_count
                FROM conversations c JOIN customers cu ON cu.id=c.customer_id
                WHERE {where} AND c.created_at >= :from_utc AND c.created_at < :to_utc
                GROUP BY 1,2
            )
            SELECT rm.platform, rm.weekday, rm.hour, rm.message_count,
                   COALESCE(cs.conversation_count, 0) AS conversation_count
            FROM ranked_messages rm LEFT JOIN conversation_slots cs
              ON cs.platform=rm.platform AND cs.hour=rm.hour WHERE rm.rn=1
        """)
        return self.db.execute(sql, self._platform_params(business_id, filters, filters.from_, filters.to)).mappings().all()

    def active_integrations(self, business_id: int):
        return self.db.query(Integration.platform).filter(
            Integration.business_id == business_id,
            Integration.status == "active",
        ).distinct().all()

    def platform_trend(self, business_id: int, filters: AnalyticsFilters, platform: str, bucket: str, metric: str):
        interval = {"hour": "1 hour", "day": "1 day", "week": "1 week", "month": "1 month"}[bucket]
        params = self._platform_params(business_id, filters, filters.from_, filters.to)
        params["selected_platform"] = platform
        if metric == "conversations":
            clauses = self._platform_sql_parts(filters) + ["LOWER(cu.platform) = :selected_platform"]
            source = "conversations c JOIN customers cu ON cu.id = c.customer_id"
            timestamp = "c.created_at"
            metric_filter = ""
        else:
            clauses = self._platform_sql_parts(filters) + ["LOWER(COALESCE(m.platform, cu.platform)) = :selected_platform"]
            source = "messages m JOIN conversations c ON c.id = m.conversation_id JOIN customers cu ON cu.id = c.customer_id"
            timestamp = "m.timestamp"
            metric_filter = {
                "messages": "", "inbound_messages": "AND LOWER(m.sender_type) = 'customer'",
                "outgoing_messages": "AND LOWER(m.sender_type) = 'agent'",
                "negative_messages": "AND LOWER(m.sentiment) = 'negative'",
            }[metric]
        sql = text(f"""
            WITH bounds AS (
                SELECT date_trunc('{bucket}', timezone(:timezone, CAST(:from_utc AS TIMESTAMPTZ))) AS first_bucket,
                       date_trunc('{bucket}', timezone(:timezone, CAST(:to_utc AS TIMESTAMPTZ) - INTERVAL '1 microsecond')) AS last_bucket
            ), buckets AS (
                SELECT generate_series(first_bucket, last_bucket, INTERVAL '{interval}') AS bucket_start FROM bounds
            ), counts AS (
                SELECT date_trunc('{bucket}', timezone(:timezone, {timestamp})) AS bucket_start, COUNT(*) AS value
                FROM {source} WHERE {' AND '.join(clauses)}
                  AND {timestamp} >= :from_utc AND {timestamp} < :to_utc {metric_filter}
                GROUP BY 1
            )
            SELECT b.bucket_start, COALESCE(c.value, 0) AS value
            FROM buckets b LEFT JOIN counts c ON c.bucket_start=b.bucket_start ORDER BY b.bucket_start
        """)
        return self.db.execute(sql, params).mappings().all()

    def customer_analytics_rows(self, business_id: int, filters: AnalyticsFilters, start: datetime, end: datetime):
        """Return one aggregate row per explicit canonical customer; never message histories."""
        clauses = ["c.business_id = :business_id"]
        if not filters.include_deleted:
            clauses.append("c.is_deleted = FALSE")
        if filters.agent_id is not None:
            clauses.append("c.assigned_agent_id = :agent_id")
        if filters.status is not None:
            clauses.append("c.status = :status")
        if filters.priority is not None:
            clauses.append("c.priority = :priority")
        if filters.platform is not None:
            clauses.append(":platform = ANY(a.platforms_used)")
        params = self._platform_params(business_id, filters, start, end)
        sql = text(f"""
            WITH RECURSIVE edges AS (
                SELECT cu.id,
                       CASE
                         WHEN ci.master_customer_id IS NOT NULL AND identity_master.id IS NOT NULL
                              AND (merge_master.id IS NULL OR merge_master.id = identity_master.id)
                           THEN identity_master.id
                         WHEN ci.master_customer_id IS NULL AND cu.is_merged = TRUE AND merge_master.id IS NOT NULL
                           THEN merge_master.id
                         ELSE NULL
                       END AS target_id,
                       (ci.master_customer_id IS NOT NULL AND identity_master.id IS NULL)
                         OR (cu.is_merged = TRUE AND cu.merged_into_id IS NOT NULL AND merge_master.id IS NULL) AS broken_link,
                       ci.master_customer_id IS NOT NULL AND merge_master.id IS NOT NULL
                         AND identity_master.id <> merge_master.id AS conflicting_link,
                       COALESCE(ci.master_customer_id, cu.merged_into_id) = cu.id AS self_link
                FROM customers cu
                LEFT JOIN customer_identities ci ON ci.linked_customer_id=cu.id AND ci.business_id=:business_id
                LEFT JOIN customers identity_master ON identity_master.id=ci.master_customer_id AND identity_master.business_id=:business_id
                LEFT JOIN customers merge_master ON merge_master.id=cu.merged_into_id AND merge_master.business_id=:business_id
                WHERE cu.business_id=:business_id
            ), walk AS (
                SELECT e.id AS original_id, e.id AS current_id, ARRAY[e.id] AS path, 0 AS depth,
                       FALSE AS cycle, e.broken_link, e.conflicting_link, e.self_link
                FROM edges e
                UNION ALL
                SELECT w.original_id, e.target_id, w.path || e.target_id, w.depth + 1,
                       e.target_id = ANY(w.path), w.broken_link OR e.broken_link,
                       w.conflicting_link OR e.conflicting_link, w.self_link OR e.self_link
                FROM walk w JOIN edges e ON e.id=w.current_id
                WHERE e.target_id IS NOT NULL AND NOT w.cycle AND NOT w.broken_link
                  AND NOT w.conflicting_link AND NOT w.self_link AND w.depth < 20
            ), resolved AS (
                SELECT DISTINCT ON (original_id) original_id,
                       CASE WHEN cycle OR broken_link OR conflicting_link OR self_link OR depth >= 20
                            THEN original_id ELSE current_id END AS canonical_id,
                       cycle OR depth >= 20 AS has_cycle, broken_link, conflicting_link, self_link
                FROM walk ORDER BY original_id, depth DESC
            ), aliases AS (
                SELECT r.canonical_id, ARRAY_AGG(DISTINCT r.original_id) AS alias_ids,
                       ARRAY_AGG(DISTINCT LOWER(cu.platform)) FILTER (WHERE cu.platform IS NOT NULL) AS platforms_used,
                       COUNT(*)::int AS alias_count,
                       BOOL_OR(r.has_cycle) AS has_cycle, BOOL_OR(r.broken_link) AS broken_link,
                       BOOL_OR(r.conflicting_link) AS conflicting_link, BOOL_OR(r.self_link) AS self_link
                FROM resolved r JOIN customers cu ON cu.id=r.original_id
                GROUP BY r.canonical_id
            ), filtered_conversations AS (
                SELECT c.*, a.canonical_id
                FROM conversations c JOIN resolved r ON r.original_id=c.customer_id
                JOIN aliases a ON a.canonical_id=r.canonical_id
                WHERE {' AND '.join(clauses)}
            ), conversation_stats AS (
                SELECT canonical_id,
                       COUNT(*) FILTER (WHERE created_at>=:from_utc AND created_at<:to_utc)::int AS total_conversations,
                       COUNT(*) FILTER (WHERE status='open')::int AS open_conversations,
                       COUNT(*) FILTER (WHERE status='pending')::int AS pending_conversations,
                       COUNT(*) FILTER (WHERE status='resolved')::int AS resolved_conversations,
                       COUNT(*) FILTER (WHERE priority='high')::int AS high_priority_conversations,
                       COUNT(*) FILTER (WHERE priority='urgent')::int AS urgent_conversations,
                       MIN(created_at) FILTER (WHERE status IN ('open','pending')) AS oldest_unresolved_at,
                       MIN(created_at) AS first_conversation_at, MAX(created_at) AS last_conversation_at
                FROM filtered_conversations GROUP BY canonical_id
            ), message_stats AS (
                SELECT fc.canonical_id,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc)::int AS total_messages,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='customer')::int AS customer_messages,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='agent')::int AS business_replies,
                       COUNT(DISTINCT DATE(timezone(:timezone,m.timestamp))) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='customer')::int AS active_days,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='customer' AND LOWER(m.sentiment)='negative')::int AS negative_customer_messages,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='customer' AND LOWER(m.sentiment) IN ('positive','neutral','negative'))::int AS classified_customer_messages,
                       COUNT(*) FILTER (WHERE m.timestamp>=:from_utc AND m.timestamp<:to_utc AND LOWER(m.sender_type)='customer' AND (m.sentiment IS NULL OR LOWER(m.sentiment) NOT IN ('positive','neutral','negative')))::int AS unclassified_customer_messages,
                       MIN(m.timestamp) FILTER (WHERE LOWER(m.sender_type)='customer') AS first_customer_message_at,
                       MAX(m.timestamp) FILTER (WHERE LOWER(m.sender_type)='customer') AS last_customer_message_at,
                       MAX(m.timestamp) FILTER (WHERE LOWER(m.sender_type)='agent') AS last_business_reply_at,
                       MAX(m.timestamp) AS last_message_at
                FROM messages m JOIN filtered_conversations fc ON fc.id=m.conversation_id
                GROUP BY fc.canonical_id
            ), latest_valid AS (
                SELECT fc.canonical_id, fc.id AS conversation_id, m.sender_type, m.timestamp,
                       ROW_NUMBER() OVER (PARTITION BY fc.id ORDER BY m.timestamp DESC, m.id DESC) AS rn
                FROM filtered_conversations fc JOIN messages m ON m.conversation_id=fc.id
                WHERE fc.status IN ('open','pending') AND LOWER(m.sender_type) IN ('customer','agent')
            ), waiting_stats AS (
                SELECT canonical_id,
                       COUNT(*) FILTER (WHERE LOWER(sender_type)='customer')::int AS waiting_conversations,
                       MIN(timestamp) FILTER (WHERE LOWER(sender_type)='customer') AS oldest_waiting_since,
                       MAX(EXTRACT(EPOCH FROM (:generated_at - timestamp))) FILTER (WHERE LOWER(sender_type)='customer') AS longest_waiting_seconds
                FROM latest_valid WHERE rn=1 GROUP BY canonical_id
            ), ordered_conversations AS (
                SELECT canonical_id, created_at,
                       LAG(created_at) OVER (PARTITION BY canonical_id ORDER BY created_at,id) AS previous_at
                FROM filtered_conversations WHERE created_at>=:from_utc AND created_at<:to_utc
            ), repeat_stats AS (
                SELECT canonical_id, COUNT(*)::int AS conversation_count,
                       COUNT(*) FILTER (WHERE previous_at IS NOT NULL AND created_at-previous_at<=INTERVAL '7 days')::int AS repeat_contact_count,
                       MIN(EXTRACT(EPOCH FROM (created_at-previous_at))) FILTER (WHERE previous_at IS NOT NULL AND created_at-previous_at<=INTERVAL '7 days') AS shortest_gap_seconds,
                       AVG(EXTRACT(EPOCH FROM (created_at-previous_at))) FILTER (WHERE previous_at IS NOT NULL AND created_at-previous_at<=INTERVAL '7 days') AS average_gap_seconds,
                       MAX(created_at) FILTER (WHERE previous_at IS NOT NULL AND created_at-previous_at<=INTERVAL '7 days') AS latest_repeat_contact_at
                FROM ordered_conversations GROUP BY canonical_id
            )
            SELECT a.canonical_id AS customer_id, COALESCE(profile.display_name,'Unknown Customer') AS display_name,
                   profile.avatar_url, profile.email, profile.phone, a.platforms_used, a.alias_count,
                   a.has_cycle, a.broken_link, a.conflicting_link, a.self_link,
                   COALESCE(cs.total_conversations,0) AS total_conversations,
                   COALESCE(ms.total_messages,0) AS total_messages,
                   COALESCE(ms.customer_messages,0) AS customer_messages,
                   COALESCE(ms.business_replies,0) AS business_replies,
                   COALESCE(ms.active_days,0) AS active_days,
                   LEAST(profile.created_at, cs.first_conversation_at, ms.first_customer_message_at) AS first_contact_at,
                   GREATEST(cs.last_conversation_at, ms.last_message_at) AS last_contact_at,
                   COALESCE(cs.open_conversations,0) AS open_conversations,
                   COALESCE(cs.pending_conversations,0) AS pending_conversations,
                   COALESCE(cs.resolved_conversations,0) AS resolved_conversations,
                   COALESCE(cs.high_priority_conversations,0) AS high_priority_conversations,
                   COALESCE(cs.urgent_conversations,0) AS urgent_conversations,
                   cs.oldest_unresolved_at,
                   COALESCE(ms.negative_customer_messages,0) AS negative_customer_messages,
                   COALESCE(ms.classified_customer_messages,0) AS classified_customer_messages,
                   COALESCE(ms.unclassified_customer_messages,0) AS unclassified_customer_messages,
                   ms.last_customer_message_at, ms.last_business_reply_at,
                   COALESCE(ws.waiting_conversations,0) AS waiting_conversations,
                   ws.oldest_waiting_since, ws.longest_waiting_seconds,
                   COALESCE(rs.conversation_count,0) AS repeat_conversation_count,
                   COALESCE(rs.repeat_contact_count,0) AS repeat_contact_count,
                   rs.shortest_gap_seconds, rs.average_gap_seconds, rs.latest_repeat_contact_at
            FROM aliases a JOIN customers profile ON profile.id=a.canonical_id
            LEFT JOIN conversation_stats cs ON cs.canonical_id=a.canonical_id
            LEFT JOIN message_stats ms ON ms.canonical_id=a.canonical_id
            LEFT JOIN waiting_stats ws ON ws.canonical_id=a.canonical_id
            LEFT JOIN repeat_stats rs ON rs.canonical_id=a.canonical_id
        """)
        params["generated_at"] = datetime.now(timezone.utc)
        return self.db.execute(sql, params).mappings().all()
