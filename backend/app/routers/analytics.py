from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_business_analytics
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsFilters, AnalyticsPlatform, AnalyticsPriority, AnalyticsStatus,
    AnalyticsSummaryResponse, ComparisonMode, MessageTrendResponse,
    CustomerActivityResponse, CustomerAnalyticsSummaryResponse, CustomerAttentionResponse,
    PlatformAnalyticsResponse, PlatformTrendResponse,
)
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["analytics"])
DEFAULT_ANALYTICS_TIMEZONE = "Asia/Kathmandu"
MAX_INTERACTIVE_RANGE = timedelta(days=366)


@dataclass
class AnalyticsRequestContext:
    user: User
    filters: AnalyticsFilters


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_analytics_context(
    from_param: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    timezone_name: str = Query(DEFAULT_ANALYTICS_TIMEZONE, alias="timezone"),
    platform: AnalyticsPlatform | None = Query(None),
    agent_id: int | None = Query(None, ge=1),
    conversation_status: AnalyticsStatus | None = Query(None, alias="status"),
    priority: AnalyticsPriority | None = Query(None),
    include_deleted: bool = Query(False),
    comparison: ComparisonMode = Query(ComparisonMode.previous_period),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_analytics),
) -> AnalyticsRequestContext:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown IANA timezone",
        ) from exc

    end = _as_utc(to or datetime.now(timezone.utc))
    start = _as_utc(from_param or (end - timedelta(days=30)))
    if start >= end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'from' must be earlier than 'to'",
        )
    if end - start > MAX_INTERACTIVE_RANGE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Analytics date range cannot exceed 366 days",
        )

    if agent_id is not None:
        agent = db.query(User.id).filter(
            User.id == agent_id,
            User.business_id == current_user.business_id,
        ).first()
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected agent is not available for this business",
            )

    filters = AnalyticsFilters(
        **{
            "from": start,
            "to": end,
            "timezone": timezone_name,
            "platform": platform,
            "agent_id": agent_id,
            "status": conversation_status,
            "priority": priority,
            "include_deleted": include_deleted,
            "comparison": comparison,
        }
    )
    return AnalyticsRequestContext(user=current_user, filters=filters)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.summary(context.user.business_id, context.filters)


@router.get("/message-trend", response_model=MessageTrendResponse)
def get_message_trend(
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.trend(context.user.business_id, context.filters)


@router.get("/platforms", response_model=PlatformAnalyticsResponse)
def get_platform_analytics(
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.platforms(context.user.business_id, context.filters)


@router.get("/platforms/{channel}/trend", response_model=PlatformTrendResponse)
def get_platform_trend(
    channel: Literal["facebook", "instagram", "email"],
    bucket: Literal["hour", "day", "week", "month"] = Query("day"),
    metric: Literal["conversations", "messages", "inbound_messages", "outgoing_messages", "negative_messages"] = Query("messages"),
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    if context.filters.platform is not None and context.filters.platform.value != channel:
        raise HTTPException(status_code=422, detail="Path platform conflicts with the analytics platform filter")
    selected_filters = context.filters.model_copy(update={"platform": AnalyticsPlatform(channel)})
    return service.platform_trend(context.user.business_id, selected_filters, channel, bucket, metric)


@router.get("/customers/summary", response_model=CustomerAnalyticsSummaryResponse)
def get_customer_analytics_summary(
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.customer_summary(context.user.business_id, context.filters)


@router.get("/customers/active", response_model=CustomerActivityResponse)
def get_active_customers(
    search: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    sort_by: Literal["total_messages", "total_conversations", "active_days", "last_contact_at", "currently_open_conversations", "negative_customer_messages"] = Query("total_messages"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.active_customers(context.user.business_id, context.filters, search, limit, offset, sort_by, sort_order)


@router.get("/customers/attention", response_model=CustomerAttentionResponse)
def get_customers_needing_attention(
    search: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    sort_by: Literal["attention_score", "longest_waiting_seconds", "unresolved_conversations", "urgent_conversations", "negative_customer_messages", "repeat_contact_count", "last_contact_at"] = Query("attention_score"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.attention_customers(context.user.business_id, context.filters, search, limit, offset, sort_by, sort_order)


@router.get("/export", response_class=Response)
def export_analytics_report(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    context: AnalyticsRequestContext = Depends(get_analytics_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    if format == "pdf":
        report = service.export_pdf(context.user.business_id, context.filters)
        filename = f"haqdesk-analytics-{context.filters.from_.date()}-to-{context.filters.to.date()}.pdf"
        return Response(
            content=report,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    report = service.export_csv(context.user.business_id, context.filters)
    filename = f"haqdesk-analytics-{context.filters.from_.date()}-to-{context.filters.to.date()}.csv"
    return Response(
        content=report,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
