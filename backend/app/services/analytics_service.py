import csv
import io
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import fitz

from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsFilters, AnalyticsSummaryMetrics, AnalyticsSummaryResponse,
    AppliedFilters, CustomerActivityItem, CustomerActivityResponse,
    CustomerAnalyticsSummaryMetrics, CustomerAnalyticsSummaryResponse,
    CustomerAttentionComponent, CustomerAttentionItem, CustomerAttentionResponse,
    DataQualityNotice, MessageTrendResponse, MetricValue, PaginationMeta,
    PlatformAnalyticsItem, PlatformAnalyticsResponse, PlatformTrendResponse, Series, TimeBucket,
)


class AnalyticsService:
    SUPPORTED_ANALYTICS_PLATFORMS = {"facebook": "Facebook", "instagram": "Instagram", "email": "Email"}
    REPEAT_CONTACT_WINDOW_DAYS = 7
    ATTENTION_SCORE_WEIGHTS = {"unresolved": 30, "waiting": 25, "negative_sentiment": 20, "repeat_contact": 10, "priority": 10, "recent_activity": 5}
    ATTENTION_LEVELS = ((75, "urgent_attention"), (50, "needs_attention"), (25, "watch"), (0, "normal"))
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    @staticmethod
    def applied(filters: AnalyticsFilters) -> AppliedFilters:
        return AppliedFilters(**filters.model_dump(by_alias=True))

    @staticmethod
    def metric(current, previous=None, *, sample_size=None, status="available", reason=None):
        if previous is None:
            return MetricValue(
                value=current, sample_size=sample_size, status=status, reason=reason
            )
        absolute = current - previous
        percentage = None if previous == 0 else round((absolute / previous) * 100, 2)
        return MetricValue(
            value=current,
            previous_value=previous,
            absolute_change=absolute,
            percentage_change=percentage,
            sample_size=sample_size,
            status=status,
            reason=reason,
        )

    def summary(self, business_id: int, filters: AnalyticsFilters) -> AnalyticsSummaryResponse:
        current_conversations = self.repository.conversation_counts(
            business_id, filters, filters.from_, filters.to
        )
        current_messages = self.repository.message_counts(
            business_id, filters, filters.from_, filters.to
        )
        current_docs, current_chunks = self.repository.knowledge_counts(
            business_id, filters.from_, filters.to
        )

        previous_conversations = previous_messages = None
        previous_docs = previous_chunks = None
        if filters.comparison.value == "previous_period":
            duration = filters.to - filters.from_
            previous_from = filters.from_ - duration
            previous_to = filters.from_
            previous_conversations = self.repository.conversation_counts(
                business_id, filters, previous_from, previous_to
            )
            previous_messages = self.repository.message_counts(
                business_id, filters, previous_from, previous_to
            )
            previous_docs, previous_chunks = self.repository.knowledge_counts(
                business_id, previous_from, previous_to
            )

        def previous(row, name):
            return getattr(row, name) if row is not None else None

        status_reason = "Conversation status is current state; status history is not stored."
        metrics = AnalyticsSummaryMetrics(
            total_conversations=self.metric(current_conversations.total, previous(previous_conversations, "total")),
            total_messages=self.metric(current_messages.total, previous(previous_messages, "total")),
            customer_messages=self.metric(current_messages.customer, previous(previous_messages, "customer")),
            agent_messages=self.metric(current_messages.agent, previous(previous_messages, "agent")),
            open_conversations=self.metric(current_conversations.open, previous(previous_conversations, "open"), status="partial", reason=status_reason),
            pending_conversations=self.metric(current_conversations.pending, previous(previous_conversations, "pending"), status="partial", reason=status_reason),
            resolved_conversations=self.metric(current_conversations.resolved, previous(previous_conversations, "resolved"), status="partial", reason=status_reason),
            total_customers=self.metric(current_conversations.customers, previous(previous_conversations, "customers")),
            knowledge_documents=self.metric(current_docs, previous_docs),
            knowledge_chunks=self.metric(current_chunks, previous_chunks),
            team_members=self.metric(
                self.repository.team_count(business_id), status="unavailable",
                reason="Team-member count is a current-state total and has no historical snapshot."
            ),
            retained_ai_drafts=self.metric(
                current_messages.drafts, previous(previous_messages, "drafts"), status="partial",
                reason="This counts messages currently retaining a draft, not durable AI generation events."
            ),
        )
        platform = self.repository.platform_distribution(business_id, filters)
        sentiment = self.repository.sentiment_distribution(business_id, filters)
        notices = [
            DataQualityNotice(metric="conversation_status", severity="info", message=status_reason),
            DataQualityNotice(metric="retained_ai_drafts", severity="warning", message=metrics.retained_ai_drafts.reason or ""),
        ]
        if filters.agent_id is not None:
            notices.append(DataQualityNotice(
                metric="agent_filter", severity="info",
                message="Agent filtering uses the conversation's current assignment; assignment history is unavailable."
            ))

        value = lambda metric: int(metric.value or 0)
        return AnalyticsSummaryResponse(
            generated_at=datetime.now(timezone.utc),
            applied_filters=self.applied(filters),
            metrics=metrics,
            platform_conversation_distribution=platform,
            sentiment_distribution=sentiment,
            data_quality_notices=notices,
            total_messages=value(metrics.total_messages),
            customer_messages=value(metrics.customer_messages),
            agent_messages=value(metrics.agent_messages),
            ai_drafts_generated=value(metrics.retained_ai_drafts),
            retained_ai_drafts=value(metrics.retained_ai_drafts),
            total_conversations=value(metrics.total_conversations),
            open_conversations=value(metrics.open_conversations),
            pending_conversations=value(metrics.pending_conversations),
            resolved_conversations=value(metrics.resolved_conversations),
            total_customers=value(metrics.total_customers),
            team_members=value(metrics.team_members),
            platform_breakdown=platform,
            sentiment_breakdown=sentiment,
            knowledge_documents=value(metrics.knowledge_documents),
            knowledge_chunks=value(metrics.knowledge_chunks),
            messages_per_day=[],
        )

    def trend(self, business_id: int, filters: AnalyticsFilters) -> MessageTrendResponse:
        duration = filters.to - filters.from_
        bucket = "hour" if duration <= timedelta(days=1) else "day" if duration <= timedelta(days=90) else "week"
        rows = self.repository.message_trend(business_id, filters, bucket)
        zone = ZoneInfo(filters.timezone)
        step = {"hour": timedelta(hours=1), "day": timedelta(days=1), "week": timedelta(weeks=1)}[bucket]
        keys = [
            ("all_messages", "All messages"),
            ("customer_messages", "Customer messages"),
            ("agent_messages", "Agent messages"),
        ]
        series = []
        for key, label in keys:
            points = []
            for row in rows:
                local_start = row["bucket_start"].replace(tzinfo=zone)
                local_end = local_start + step
                points.append(TimeBucket(
                    start=local_start,
                    end=local_end,
                    label=local_start.isoformat(),
                    value=int(row[key]),
                ))
            series.append(Series(key=key, label=label, total=sum(point.value for point in points), points=points))
        return MessageTrendResponse(
            generated_at=datetime.now(timezone.utc),
            applied_filters=self.applied(filters),
            bucket=bucket,
            series=series,
        )

    def platforms(self, business_id: int, filters: AnalyticsFilters) -> PlatformAnalyticsResponse:
        current_rows = {row["platform"]: dict(row) for row in self.repository.platform_period_stats(business_id, filters, filters.from_, filters.to)}
        duration = filters.to - filters.from_
        previous_rows = {}
        if filters.comparison.value == "previous_period":
            previous_rows = {row["platform"]: dict(row) for row in self.repository.platform_period_stats(
                business_id, filters, filters.from_ - duration, filters.from_
            )}
        backlog = {row["platform"]: dict(row) for row in self.repository.platform_backlog(business_id, filters)}
        response = {row["platform"]: dict(row) for row in self.repository.platform_response_times(business_id, filters, filters.from_, filters.to)}
        previous_response = {}
        if filters.comparison.value == "previous_period":
            previous_response = {row["platform"]: dict(row) for row in self.repository.platform_response_times(
                business_id, filters, filters.from_ - duration, filters.from_
            )}
        peaks = {row["platform"]: dict(row) for row in self.repository.platform_peaks(business_id, filters)}
        connected_values = {str(row[0]).lower() for row in self.repository.active_integrations(business_id)}
        observed = set(current_rows)
        requested = filters.platform.value if filters.platform else None
        active = ((observed | connected_values) & set(self.SUPPORTED_ANALYTICS_PLATFORMS))
        if requested:
            active &= {requested}

        notices = []
        unsupported = (observed | connected_values) - set(self.SUPPORTED_ANALYTICS_PLATFORMS)
        for platform in sorted(unsupported):
            notices.append(DataQualityNotice(
                metric="unsupported_platform", severity="warning",
                message=f"{platform.title()} records were excluded because the channel is not verified for Platform Analytics."
            ))
        if "whatsapp" in connected_values:
            notices.append(DataQualityNotice(
                metric="whatsapp_connection", severity="warning",
                message="A stale WhatsApp integration record exists, but WhatsApp is not a verified operational channel and was excluded."
            ))
        canonical_notice = DataQualityNotice(
            metric="unique_customers", severity="info",
            message="Customer counts use explicit merge and identity links only; unlinked cross-platform aliases may remain separate."
        )
        notices.append(canonical_notice)

        totals = {key: sum(int(current_rows.get(name, {}).get(key, 0) or 0) for name in active)
                  for key in ("conversations", "messages", "unique_customers")}
        previous_totals = {key: sum(int(previous_rows.get(name, {}).get(key, 0) or 0) for name in active)
                           for key in ("conversations", "messages", "unique_customers")}

        def value(row, key):
            raw = row.get(key, 0) if row else 0
            return float(raw) if raw is not None else None

        def compared(name, key, *, status="available", reason=None):
            current = value(current_rows.get(name), key) or 0
            previous = value(previous_rows.get(name), key) if previous_rows else None
            return self.metric(current, previous, status=status, reason=reason)

        def share(name, key):
            current = value(current_rows.get(name), key) or 0
            current_share = round(current / totals[key] * 100, 2) if totals[key] else 0
            previous_share = None
            if previous_rows:
                previous = value(previous_rows.get(name), key) or 0
                previous_share = round(previous / previous_totals[key] * 100, 2) if previous_totals[key] else 0
            return self.metric(current_share, previous_share)

        status_reason = "Backlog is a current-state snapshot; historical status and assignment changes are not stored."
        response_reason = "Sent agent messages include human and successfully sent automated replies; older records do not reliably distinguish them."
        weekdays = {1: "monday", 2: "tuesday", 3: "wednesday", 4: "thursday", 5: "friday", 6: "saturday", 7: "sunday"}
        items = []
        for name in sorted(active):
            row = current_rows.get(name, {})
            old = previous_rows.get(name, {})
            back = backlog.get(name, {})
            resp = response.get(name, {})
            old_resp = previous_response.get(name, {})
            peak = peaks.get(name, {})
            classified = sum(int(row.get(key, 0) or 0) for key in ("positive_messages", "neutral_messages", "negative_messages"))
            old_classified = sum(int(old.get(key, 0) or 0) for key in ("positive_messages", "neutral_messages", "negative_messages"))
            negative_rate = round(int(row.get("negative_messages", 0) or 0) / classified * 100, 2) if classified else 0
            old_negative_rate = round(int(old.get("negative_messages", 0) or 0) / old_classified * 100, 2) if old_classified else 0
            backlog_metric = lambda key: self.metric(int(back.get(key, 0) or 0), status="unavailable", reason=status_reason)
            response_metric = lambda key: self.metric(
                round(float(resp[key]), 2) if resp.get(key) is not None else None,
                round(float(old_resp[key]), 2) if old_resp.get(key) is not None else None,
                sample_size=int(resp.get("sample_size", 0) or 0), status="partial", reason=response_reason,
            )
            items.append(PlatformAnalyticsItem(
                platform=name, display_name=self.SUPPORTED_ANALYTICS_PLATFORMS[name],
                is_connected=name in connected_values,
                conversations=compared(name, "conversations"), messages=compared(name, "messages"),
                inbound_messages=compared(name, "inbound_messages"), outgoing_messages=compared(name, "outgoing_messages"),
                unique_customers=compared(name, "unique_customers"),
                conversation_share_percentage=share(name, "conversations"), message_share_percentage=share(name, "messages"),
                customer_share_percentage=share(name, "unique_customers"),
                open_conversations=backlog_metric("open"), pending_conversations=backlog_metric("pending"),
                resolved_conversations=backlog_metric("resolved"), unassigned_conversations=backlog_metric("unassigned"),
                high_priority_conversations=backlog_metric("high_priority"), urgent_priority_conversations=backlog_metric("urgent_priority"),
                positive_messages=compared(name, "positive_messages"), neutral_messages=compared(name, "neutral_messages"),
                negative_messages=compared(name, "negative_messages"), unclassified_messages=compared(name, "unclassified_messages"),
                negative_sentiment_rate=self.metric(negative_rate, old_negative_rate, sample_size=classified),
                classified_sentiment_sample_size=classified,
                average_first_response_seconds=response_metric("average_seconds"),
                median_first_response_seconds=response_metric("median_seconds"), p90_first_response_seconds=response_metric("p90_seconds"),
                response_sample_size=int(resp.get("sample_size", 0) or 0),
                unanswered_conversations=self.metric(int(resp.get("unanswered", 0) or 0), int(old_resp.get("unanswered", 0) or 0) if previous_response else None),
                peak_weekday=weekdays.get(peak.get("weekday")), peak_hour=int(peak["hour"]) if peak.get("hour") is not None else None,
                peak_hour_message_count=int(peak.get("message_count", 0) or 0),
                peak_hour_conversation_count=int(peak.get("conversation_count", 0) or 0),
                data_quality=[canonical_notice, DataQualityNotice(metric="first_response", severity="warning", message=response_reason)],
            ))

        insights = []
        if items:
            highest = max(items, key=lambda item: item.conversations.value or 0)
            insights.append(f"{highest.display_name} received the highest number of conversations in the selected period.")
            backlog_item = max(items, key=lambda item: (item.open_conversations.value or 0) + (item.pending_conversations.value or 0))
            insights.append(f"{backlog_item.display_name} has the largest current unresolved backlog among the displayed channels.")
            classified_items = [item for item in items if item.classified_sentiment_sample_size]
            if classified_items:
                negative = max(classified_items, key=lambda item: item.negative_sentiment_rate.value or 0)
                insights.append(f"{negative.display_name} has the highest negative-sentiment rate among classified messages.")
        return PlatformAnalyticsResponse(
            generated_at=datetime.now(timezone.utc), applied_filters=self.applied(filters),
            platforms=items, data_quality=notices, insights=insights,
        )

    def platform_trend(self, business_id: int, filters: AnalyticsFilters, platform: str, bucket: str, metric: str) -> PlatformTrendResponse:
        rows = self.repository.platform_trend(business_id, filters, platform, bucket, metric)
        zone = ZoneInfo(filters.timezone)
        if bucket == "month":
            def next_bucket(value):
                return value.replace(year=value.year + 1, month=1) if value.month == 12 else value.replace(month=value.month + 1)
        else:
            step = {"hour": timedelta(hours=1), "day": timedelta(days=1), "week": timedelta(weeks=1)}[bucket]
            next_bucket = lambda value: value + step
        points = []
        for row in rows:
            start = row["bucket_start"].replace(tzinfo=zone)
            points.append(TimeBucket(start=start, end=next_bucket(start), label=start.isoformat(), value=int(row["value"])))
        return PlatformTrendResponse(
            generated_at=datetime.now(timezone.utc), applied_filters=self.applied(filters), platform=platform,
            bucket=bucket, metric=metric,
            series=Series(key=metric, label=metric.replace("_", " ").title(), total=sum(point.value for point in points), points=points),
        )

    @staticmethod
    def _customer_notices(row=None):
        notices = [
            DataQualityNotice(metric="customer_identity", severity="info", message="Customers are combined only through explicit merge and identity links; unlinked aliases may remain separate."),
            DataQualityNotice(metric="snapshot_metrics", severity="info", message="Open work, priority, and assignment use the current conversation state rather than historical state."),
            DataQualityNotice(metric="repeat_contact", severity="info", message="Repeat contact means the customer opened another conversation within seven days. It does not necessarily mean the same issue occurred again."),
            DataQualityNotice(metric="outgoing_metadata", severity="warning", message="Older business replies may not reliably distinguish human and automated responses."),
        ]
        if row:
            for key, message in (
                ("has_cycle", "A customer merge cycle was isolated and not combined."),
                ("broken_link", "A broken customer merge reference was isolated and not combined."),
                ("conflicting_link", "Conflicting customer identity links were isolated and not combined."),
                ("self_link", "A customer record linked to itself was isolated and not combined."),
            ):
                if row.get(key):
                    notices.append(DataQualityNotice(metric="customer_identity", severity="warning", message=message))
            if int(row.get("unclassified_customer_messages", 0) or 0):
                notices.append(DataQualityNotice(metric="customer_sentiment", severity="info", message="Some customer messages have not yet been analyzed for sentiment."))
        return notices

    @staticmethod
    def _waiting_normalized(seconds):
        if not seconds or seconds <= 0: return 0.0
        if seconds < 900: return 0.1
        if seconds < 3600: return 0.25 + (seconds - 900) / 2700 * 0.25
        if seconds < 14400: return 0.5 + (seconds - 3600) / 10800 * 0.25
        if seconds < 86400: return 0.75 + (seconds - 14400) / 72000 * 0.25
        return 1.0

    def _attention(self, row, generated_at):
        open_count = int(row.get("open_conversations", 0) or 0)
        pending = int(row.get("pending_conversations", 0) or 0)
        unresolved = open_count + pending
        oldest = row.get("oldest_unresolved_at")
        unresolved_age = max(0, (generated_at - oldest).total_seconds()) if oldest else 0
        unresolved_norm = min(1.0, min(unresolved / 3, 1) * 0.7 + min(unresolved_age / 604800, 1) * 0.3)
        waiting_count = int(row.get("waiting_conversations", 0) or 0)
        longest_wait = float(row.get("longest_waiting_seconds") or 0)
        waiting_norm = min(1.0, self._waiting_normalized(longest_wait) * 0.8 + min(waiting_count / 3, 1) * 0.2)
        negative = int(row.get("negative_customer_messages", 0) or 0)
        classified = int(row.get("classified_customer_messages", 0) or 0)
        negative_rate = negative / classified if classified else 0
        negative_norm = min(1.0, negative_rate * 0.6 + min(negative / 5, 1) * 0.4)
        repeats = int(row.get("repeat_contact_count", 0) or 0)
        repeat_norm = min(repeats / 3, 1)
        urgent = int(row.get("urgent_conversations", 0) or 0)
        high = int(row.get("high_priority_conversations", 0) or 0)
        priority_norm = min(1.0, urgent * 0.7 + high * 0.3)
        last_customer = row.get("last_customer_message_at")
        recent_seconds = (generated_at - last_customer).total_seconds() if last_customer else None
        recent_norm = 1.0 if unresolved and recent_seconds is not None and recent_seconds <= 86400 else 0.5 if unresolved and recent_seconds is not None and recent_seconds <= 604800 else 0.0
        values = [
            ("unresolved", "Open customer issues", unresolved, unresolved_norm, f"{unresolved} conversations are currently open or pending."),
            ("waiting", "Waiting for reply", longest_wait, waiting_norm, f"The longest unanswered customer message has waited {round(longest_wait / 3600, 1)} hours." if waiting_count else "No conversation is currently waiting for a business reply."),
            ("negative_sentiment", "Negative customer messages", negative, negative_norm, f"{negative} negative customer messages were recorded in the selected period."),
            ("repeat_contact", "Repeat contact", repeats, repeat_norm, f"The customer opened another conversation within seven days {repeats} times."),
            ("priority", "Conversation priority", urgent * 2 + high, priority_norm, f"Current work includes {urgent} urgent and {high} high-priority conversations."),
            ("recent_activity", "Recent customer activity", 1 if recent_norm else 0, recent_norm, "Recent customer activity is paired with currently open support work." if recent_norm else "No recent customer activity is paired with open work."),
        ]
        components = []
        for key, label, raw, normalized, explanation in values:
            weight = self.ATTENTION_SCORE_WEIGHTS[key]
            components.append(CustomerAttentionComponent(key=key, label=label, raw_value=round(float(raw), 2), normalized_value=round(normalized, 3), maximum_weight=weight, contribution=round(normalized * weight, 2), explanation=explanation))
        score = min(100.0, round(sum(item.contribution for item in components), 1))
        level = next(name for threshold, name in self.ATTENTION_LEVELS if score >= threshold)
        reasons = []
        if unresolved: reasons.append(f"{unresolved} currently open conversation{'s' if unresolved != 1 else ''}")
        if waiting_count: reasons.append(f"{waiting_count} conversation{'s are' if waiting_count != 1 else ' is'} waiting for a business reply")
        if longest_wait: reasons.append(f"Longest unanswered customer message has waited {round(longest_wait / 3600, 1)} hours")
        if negative: reasons.append(f"{negative} negative customer message{'s' if negative != 1 else ''} in the selected period")
        if repeats: reasons.append(f"Customer made {repeats} repeat contact{'s' if repeats != 1 else ''} within seven days")
        if urgent: reasons.append(f"{urgent} urgent conversation{'s' if urgent != 1 else ''}")
        return score, level, components, reasons[:4]

    def _activity_item(self, row):
        conversations = int(row.get("total_conversations", 0) or 0)
        messages = int(row.get("total_messages", 0) or 0)
        return CustomerActivityItem(
            customer_id=row["customer_id"], display_name=row["display_name"], avatar_url=row.get("avatar_url"), email=row.get("email"), phone=row.get("phone"),
            platforms_used=list(row.get("platforms_used") or []), alias_count=max(0, int(row.get("alias_count", 1)) - 1),
            total_conversations=conversations, total_messages=messages, customer_messages=int(row.get("customer_messages", 0) or 0), business_replies=int(row.get("business_replies", 0) or 0), active_days=int(row.get("active_days", 0) or 0),
            first_contact_at=row.get("first_contact_at"), last_contact_at=row.get("last_contact_at"), currently_open_conversations=int(row.get("open_conversations", 0) or 0) + int(row.get("pending_conversations", 0) or 0), pending_conversations=int(row.get("pending_conversations", 0) or 0), resolved_conversations=int(row.get("resolved_conversations", 0) or 0), high_priority_conversations=int(row.get("high_priority_conversations", 0) or 0), urgent_conversations=int(row.get("urgent_conversations", 0) or 0),
            negative_customer_messages=int(row.get("negative_customer_messages", 0) or 0), not_yet_analyzed_customer_messages=int(row.get("unclassified_customer_messages", 0) or 0), average_messages_per_conversation=round(messages / conversations, 2) if conversations else 0,
            waiting_for_reply=bool(row.get("waiting_conversations")), conversations_waiting_for_reply=int(row.get("waiting_conversations", 0) or 0), longest_waiting_seconds=float(row["longest_waiting_seconds"]) if row.get("longest_waiting_seconds") is not None else None, oldest_waiting_since=row.get("oldest_waiting_since"), last_customer_message_at=row.get("last_customer_message_at"), last_business_reply_at=row.get("last_business_reply_at"),
            repeat_contact_count=int(row.get("repeat_contact_count", 0) or 0), shortest_gap_seconds=float(row["shortest_gap_seconds"]) if row.get("shortest_gap_seconds") is not None else None, average_gap_seconds=float(row["average_gap_seconds"]) if row.get("average_gap_seconds") is not None else None, latest_repeat_contact_at=row.get("latest_repeat_contact_at"), data_quality=self._customer_notices(row),
        )

    def customer_summary(self, business_id: int, filters: AnalyticsFilters):
        now = datetime.now(timezone.utc)
        rows = self.repository.customer_analytics_rows(business_id, filters, filters.from_, filters.to)
        duration = filters.to - filters.from_
        previous_rows = self.repository.customer_analytics_rows(business_id, filters, filters.from_ - duration, filters.from_) if filters.comparison.value == "previous_period" else []
        def stats(values, period_start, period_end):
            active = [r for r in values if int(r.get("total_conversations",0) or 0) or int(r.get("total_messages",0) or 0)]
            scored = [self._attention(r, now)[0] for r in values]
            return {
                "active": len(active), "new": sum(1 for r in active if r.get("first_contact_at") and period_start <= r["first_contact_at"] < period_end),
                "returning": sum(1 for r in active if r.get("first_contact_at") and r["first_contact_at"] < period_start),
                "open": sum(1 for r in values if int(r.get("open_conversations",0) or 0)+int(r.get("pending_conversations",0) or 0)>0),
                "waiting": sum(1 for r in values if int(r.get("waiting_conversations",0) or 0)>0), "attention": sum(1 for score in scored if score>=50), "urgent": sum(1 for score in scored if score>=75),
                "repeat": sum(1 for r in active if int(r.get("repeat_contact_count",0) or 0)>0),
                "avg_conv": round(sum(int(r.get("total_conversations",0) or 0) for r in active)/len(active),2) if active else 0,
                "avg_msg": round(sum(int(r.get("total_messages",0) or 0) for r in active)/len(active),2) if active else 0,
            }
        current = stats(rows, filters.from_, filters.to)
        previous = stats(previous_rows, filters.from_ - duration, filters.from_) if previous_rows else None
        compared = lambda key: self.metric(current[key], previous[key] if previous else None)
        snapshot = lambda key: self.metric(current[key], status="partial", reason="This is a current snapshot; historical status changes are not stored.")
        return CustomerAnalyticsSummaryResponse(generated_at=now, applied_filters=self.applied(filters), metrics=CustomerAnalyticsSummaryMetrics(
            active_customers=compared("active"), new_customers=compared("new"), returning_customers=compared("returning"),
            customers_with_open_conversations=snapshot("open"), customers_waiting_for_reply=snapshot("waiting"), customers_needing_attention=snapshot("attention"), customers_with_urgent_attention=snapshot("urgent"), repeat_contact_customers=compared("repeat"), average_conversations_per_customer=compared("avg_conv"), average_messages_per_customer=compared("avg_msg")), data_quality=self._customer_notices())

    def active_customers(self, business_id, filters, search, limit, offset, sort_by, sort_order):
        rows = self.repository.customer_analytics_rows(business_id, filters, filters.from_, filters.to)
        rows = [r for r in rows if int(r.get("total_conversations",0) or 0) or int(r.get("total_messages",0) or 0)]
        if search:
            term = search.casefold(); rows = [r for r in rows if any(term in str(r.get(key) or "").casefold() for key in ("display_name","email","phone"))]
        key_map = {"total_messages":"total_messages","total_conversations":"total_conversations","active_days":"active_days","last_contact_at":"last_contact_at","currently_open_conversations":"open_conversations","negative_customer_messages":"negative_customer_messages"}
        rows.sort(key=lambda r: (r.get(key_map[sort_by]) is not None, r.get(key_map[sort_by]) or 0), reverse=sort_order=="desc")
        total=len(rows); items=[self._activity_item(r) for r in rows[offset:offset+limit]]
        insights=[f"{items[0].display_name} had the most activity in this view."] if items else []
        return CustomerActivityResponse(generated_at=datetime.now(timezone.utc), applied_filters=self.applied(filters), customers=items, pagination=PaginationMeta(limit=limit,offset=offset,total=total,has_more=offset+limit<total), data_quality=self._customer_notices(), insights=insights)

    def attention_customers(self, business_id, filters, search, limit, offset, sort_by, sort_order):
        now=datetime.now(timezone.utc); rows=self.repository.customer_analytics_rows(business_id, filters, filters.from_, filters.to); items=[]
        for row in rows:
            if search and not any(search.casefold() in str(row.get(key) or "").casefold() for key in ("display_name","email","phone")): continue
            score, level, components, reasons=self._attention(row,now)
            if score < 25: continue
            items.append(CustomerAttentionItem(customer_id=row["customer_id"],display_name=row["display_name"],avatar_url=row.get("avatar_url"),platforms_used=list(row.get("platforms_used") or []),attention_score=score,attention_level=level,primary_reasons=reasons,component_breakdown=components,unresolved_conversation_count=int(row.get("open_conversations",0) or 0)+int(row.get("pending_conversations",0) or 0),pending_conversation_count=int(row.get("pending_conversations",0) or 0),waiting_conversation_count=int(row.get("waiting_conversations",0) or 0),longest_waiting_seconds=float(row["longest_waiting_seconds"]) if row.get("longest_waiting_seconds") is not None else None,oldest_unresolved_at=row.get("oldest_unresolved_at"),negative_customer_message_count=int(row.get("negative_customer_messages",0) or 0),classified_sentiment_sample_size=int(row.get("classified_customer_messages",0) or 0),repeat_contact_count=int(row.get("repeat_contact_count",0) or 0),urgent_conversation_count=int(row.get("urgent_conversations",0) or 0),high_priority_conversation_count=int(row.get("high_priority_conversations",0) or 0),last_contact_at=row.get("last_contact_at"),data_quality=self._customer_notices(row)))
        key=lambda item:{"attention_score":item.attention_score,"longest_waiting_seconds":item.longest_waiting_seconds or 0,"unresolved_conversations":item.unresolved_conversation_count,"urgent_conversations":item.urgent_conversation_count,"negative_customer_messages":item.negative_customer_message_count,"repeat_contact_count":item.repeat_contact_count,"last_contact_at":item.last_contact_at or datetime.min.replace(tzinfo=timezone.utc)}[sort_by]
        items.sort(key=key,reverse=sort_order=="desc"); total=len(items)
        return CustomerAttentionResponse(generated_at=now,applied_filters=self.applied(filters),customers=items[offset:offset+limit],pagination=PaginationMeta(limit=limit,offset=offset,total=total,has_more=offset+limit<total),data_quality=self._customer_notices())

    def export_csv(self, business_id: int, filters: AnalyticsFilters) -> str:
        """Build an Excel-compatible filtered report using aggregate tenant data."""
        summary = self.summary(business_id, filters)
        trend = self.trend(business_id, filters)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["HaqDesk AI Analytics Report"])
        writer.writerow(["Generated at", summary.generated_at.isoformat()])
        writer.writerow([])
        writer.writerow(["Applied filters"])
        for key, value in summary.applied_filters.model_dump(by_alias=True).items():
            writer.writerow([key, value.isoformat() if isinstance(value, datetime) else value])
        writer.writerow([])
        writer.writerow(["Summary metrics"])
        writer.writerow(["Metric", "Value", "Previous value", "Absolute change", "Percentage change", "Status", "Reason"])
        for key, metric in summary.metrics:
            writer.writerow([key, metric.value, metric.previous_value, metric.absolute_change, metric.percentage_change, metric.status, metric.reason])
        writer.writerow([])
        writer.writerow(["Platform conversation distribution"])
        writer.writerow(["Platform", "Conversations"])
        for platform, count in sorted(summary.platform_conversation_distribution.items()):
            writer.writerow([platform, count])
        writer.writerow([])
        writer.writerow(["Sentiment distribution"])
        writer.writerow(["Sentiment", "Messages"])
        for sentiment, count in sorted(summary.sentiment_distribution.items()):
            writer.writerow([sentiment, count])
        writer.writerow([])
        writer.writerow(["Message volume trend"])
        writer.writerow(["Bucket start", "Bucket end", "All messages", "Customer messages", "Agent messages"])
        series_by_key = {series.key: series for series in trend.series}
        for index, point in enumerate(series_by_key["all_messages"].points):
            writer.writerow([point.start.isoformat(), point.end.isoformat(), point.value, series_by_key["customer_messages"].points[index].value, series_by_key["agent_messages"].points[index].value])
        writer.writerow([])
        writer.writerow(["Data quality notices"])
        writer.writerow(["Metric", "Severity", "Message"])
        for notice in summary.data_quality_notices:
            writer.writerow([notice.metric, notice.severity, notice.message])
        return "\ufeff" + output.getvalue()

    def export_pdf(self, business_id: int, filters: AnalyticsFilters) -> bytes:
        """Create a branded, paginated PDF from the same secured aggregates as the UI."""
        summary = self.summary(business_id, filters)
        trend = self.trend(business_id, filters)
        document = fitz.open()
        page = None
        y = 0.0
        navy = (0.055, 0.09, 0.16)
        blue = (0.18, 0.48, 0.95)
        muted = (0.38, 0.43, 0.52)
        border = (0.84, 0.87, 0.92)

        def new_page():
            nonlocal page, y
            page = document.new_page(width=595, height=842)
            page.draw_rect(page.rect, color=None, fill=(0.98, 0.985, 1))
            page.draw_rect(fitz.Rect(0, 0, 595, 72), color=None, fill=navy)
            page.insert_text((36, 34), "HaqDesk AI", fontsize=18, fontname="helv", color=(1, 1, 1))
            page.insert_text((36, 55), "Analytics Report", fontsize=10, fontname="helv", color=(0.67, 0.75, 0.88))
            y = 98.0

        def ensure(height: float):
            if page is None or y + height > 790:
                new_page()

        def heading(label: str):
            nonlocal y
            ensure(35)
            page.insert_text((36, y), label, fontsize=14, fontname="hebo", color=navy)
            page.draw_line((36, y + 8), (559, y + 8), color=blue, width=1.2)
            y += 27

        def row(label: str, value, *, shade=False):
            nonlocal y
            display = "-" if value is None or value == "" else str(value)
            value_lines = max(1, math.ceil(fitz.get_text_length(display, fontname="helv", fontsize=8.5) / 300))
            height = max(20, 11 * value_lines + 7)
            ensure(height + 3)
            if shade:
                page.draw_rect(fitz.Rect(36, y - 13, 559, y - 13 + height), color=None, fill=(0.94, 0.96, 0.99))
            page.insert_text((43, y), str(label).replace("_", " ").title(), fontsize=8.5, color=muted)
            page.insert_textbox(fitz.Rect(245, y - 11, 552, y - 13 + height), display, fontsize=8.5, fontname="helv", color=navy, align=fitz.TEXT_ALIGN_RIGHT)
            y += height

        new_page()
        page.insert_text((36, y), "Support performance overview", fontsize=22, fontname="hebo", color=navy)
        y += 22
        page.insert_text((36, y), f"Generated {summary.generated_at.strftime('%Y-%m-%d %H:%M UTC')}", fontsize=9, color=muted)
        y += 32

        heading("Applied filters")
        for index, (key, value) in enumerate(summary.applied_filters.model_dump(by_alias=True).items()):
            row(key, value.isoformat() if isinstance(value, datetime) else value, shade=index % 2 == 0)

        heading("Summary metrics")
        for index, (key, metric) in enumerate(summary.metrics):
            comparison = ""
            if metric.previous_value is not None:
                percentage = "n/a" if metric.percentage_change is None else f"{metric.percentage_change:+g}%"
                comparison = f" | previous {metric.previous_value} | {percentage}"
            row(key, f"{metric.value if metric.value is not None else '-'}{comparison} | {metric.status}", shade=index % 2 == 0)

        heading("Channel performance")
        if summary.platform_conversation_distribution:
            for index, (name, count) in enumerate(sorted(summary.platform_conversation_distribution.items())):
                row(name, f"{count} conversations", shade=index % 2 == 0)
        else:
            row("Result", "No channel data")

        heading("Customer sentiment")
        if summary.sentiment_distribution:
            for index, (name, count) in enumerate(sorted(summary.sentiment_distribution.items())):
                row(name, f"{count} messages", shade=index % 2 == 0)
        else:
            row("Result", "No sentiment data")

        heading("Message volume trend")
        series_by_key = {series.key: series for series in trend.series}
        all_points = series_by_key["all_messages"].points
        if all_points:
            for index, point in enumerate(all_points):
                detail = (
                    f"All {point.value} | Customer {series_by_key['customer_messages'].points[index].value}"
                    f" | Agent {series_by_key['agent_messages'].points[index].value}"
                )
                row(point.start.strftime("%Y-%m-%d %H:%M"), detail, shade=index % 2 == 0)
        else:
            row("Result", "No messages in this period")

        heading("Data quality notes")
        for index, notice in enumerate(summary.data_quality_notices):
            row(f"{notice.severity}: {notice.metric}", notice.message, shade=index % 2 == 0)

        page_count = document.page_count
        for number, report_page in enumerate(document, start=1):
            report_page.draw_line((36, 810), (559, 810), color=border, width=0.6)
            report_page.insert_text((36, 826), "Confidential business analytics", fontsize=7.5, color=muted)
            report_page.insert_text((520, 826), f"{number} / {page_count}", fontsize=7.5, color=muted)
        content = document.tobytes(garbage=4, deflate=True)
        document.close()
        return content
