from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsPlatform(str, Enum):
    facebook = "facebook"
    instagram = "instagram"
    whatsapp = "whatsapp"
    email = "email"


class AnalyticsStatus(str, Enum):
    open = "open"
    pending = "pending"
    resolved = "resolved"
    closed = "closed"


class AnalyticsPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ComparisonMode(str, Enum):
    none = "none"
    previous_period = "previous_period"


class AnalyticsFilters(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime
    timezone: str
    platform: AnalyticsPlatform | None = None
    agent_id: int | None = None
    status: AnalyticsStatus | None = None
    priority: AnalyticsPriority | None = None
    include_deleted: bool = False
    comparison: ComparisonMode = ComparisonMode.previous_period

    model_config = {"populate_by_name": True}


class AppliedFilters(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime
    timezone: str
    platform: str | None = None
    agent_id: int | None = None
    status: str | None = None
    priority: str | None = None
    include_deleted: bool
    comparison: str

    model_config = {"populate_by_name": True}


class MetricValue(BaseModel):
    value: int | float | None
    previous_value: int | float | None = None
    absolute_change: int | float | None = None
    percentage_change: float | None = None
    sample_size: int | None = None
    status: Literal["available", "partial", "unavailable"] = "available"
    reason: str | None = None


class DataQualityNotice(BaseModel):
    metric: str
    severity: Literal["info", "warning"]
    message: str


class TimeBucket(BaseModel):
    start: datetime
    end: datetime
    label: str
    value: int


class Series(BaseModel):
    key: str
    label: str
    total: int
    points: list[TimeBucket]


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int
    has_more: bool


class AnalyticsSummaryMetrics(BaseModel):
    total_conversations: MetricValue
    total_messages: MetricValue
    customer_messages: MetricValue
    agent_messages: MetricValue
    open_conversations: MetricValue
    pending_conversations: MetricValue
    resolved_conversations: MetricValue
    total_customers: MetricValue
    knowledge_documents: MetricValue
    knowledge_chunks: MetricValue
    team_members: MetricValue
    retained_ai_drafts: MetricValue


class AnalyticsSummaryResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    metrics: AnalyticsSummaryMetrics
    platform_conversation_distribution: dict[str, int]
    sentiment_distribution: dict[str, int]
    data_quality_notices: list[DataQualityNotice]

    # Temporary compatibility fields for existing dashboard consumers.
    total_messages: int
    customer_messages: int
    agent_messages: int
    ai_drafts_generated: int
    retained_ai_drafts: int
    total_conversations: int
    open_conversations: int
    pending_conversations: int
    resolved_conversations: int
    total_customers: int
    team_members: int
    platform_breakdown: dict[str, int]
    sentiment_breakdown: dict[str, int]
    knowledge_documents: int
    knowledge_chunks: int
    messages_per_day: list[dict[str, str | int]] = Field(default_factory=list)


class MessageTrendResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    bucket: Literal["hour", "day", "week", "month"]
    series: list[Series]


class PlatformAnalyticsItem(BaseModel):
    platform: str
    display_name: str
    is_connected: bool
    conversations: MetricValue
    messages: MetricValue
    inbound_messages: MetricValue
    outgoing_messages: MetricValue
    unique_customers: MetricValue
    conversation_share_percentage: MetricValue
    message_share_percentage: MetricValue
    customer_share_percentage: MetricValue
    open_conversations: MetricValue
    pending_conversations: MetricValue
    resolved_conversations: MetricValue
    unassigned_conversations: MetricValue
    high_priority_conversations: MetricValue
    urgent_priority_conversations: MetricValue
    positive_messages: MetricValue
    neutral_messages: MetricValue
    negative_messages: MetricValue
    unclassified_messages: MetricValue
    negative_sentiment_rate: MetricValue
    classified_sentiment_sample_size: int
    average_first_response_seconds: MetricValue
    median_first_response_seconds: MetricValue
    p90_first_response_seconds: MetricValue
    response_sample_size: int
    unanswered_conversations: MetricValue
    peak_weekday: str | None
    peak_hour: int | None
    peak_hour_message_count: int
    peak_hour_conversation_count: int
    data_quality: list[DataQualityNotice]


class PlatformAnalyticsResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    platforms: list[PlatformAnalyticsItem]
    data_quality: list[DataQualityNotice]
    insights: list[str]


class PlatformTrendResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    platform: str
    bucket: Literal["hour", "day", "week", "month"]
    metric: Literal["conversations", "messages", "inbound_messages", "outgoing_messages", "negative_messages"]
    series: Series


class CustomerAnalyticsSummaryMetrics(BaseModel):
    active_customers: MetricValue
    new_customers: MetricValue
    returning_customers: MetricValue
    customers_with_open_conversations: MetricValue
    customers_waiting_for_reply: MetricValue
    customers_needing_attention: MetricValue
    customers_with_urgent_attention: MetricValue
    repeat_contact_customers: MetricValue
    average_conversations_per_customer: MetricValue
    average_messages_per_customer: MetricValue


class CustomerAnalyticsSummaryResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    metrics: CustomerAnalyticsSummaryMetrics
    data_quality: list[DataQualityNotice]


class CustomerActivityItem(BaseModel):
    customer_id: int
    display_name: str
    avatar_url: str | None = None
    email: str | None = None
    phone: str | None = None
    platforms_used: list[str]
    alias_count: int
    total_conversations: int
    total_messages: int
    customer_messages: int
    business_replies: int
    active_days: int
    first_contact_at: datetime | None = None
    last_contact_at: datetime | None = None
    currently_open_conversations: int
    pending_conversations: int
    resolved_conversations: int
    high_priority_conversations: int
    urgent_conversations: int
    negative_customer_messages: int
    not_yet_analyzed_customer_messages: int
    average_messages_per_conversation: float
    waiting_for_reply: bool
    conversations_waiting_for_reply: int
    longest_waiting_seconds: float | None = None
    oldest_waiting_since: datetime | None = None
    last_customer_message_at: datetime | None = None
    last_business_reply_at: datetime | None = None
    repeat_contact_count: int
    shortest_gap_seconds: float | None = None
    average_gap_seconds: float | None = None
    latest_repeat_contact_at: datetime | None = None
    data_quality: list[DataQualityNotice]


class CustomerActivityResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    customers: list[CustomerActivityItem]
    pagination: PaginationMeta
    data_quality: list[DataQualityNotice]
    insights: list[str]


class CustomerAttentionComponent(BaseModel):
    key: str
    label: str
    raw_value: float
    normalized_value: float
    maximum_weight: float
    contribution: float
    explanation: str


class CustomerAttentionItem(BaseModel):
    customer_id: int
    display_name: str
    avatar_url: str | None = None
    platforms_used: list[str]
    attention_score: float
    attention_level: Literal["normal", "watch", "needs_attention", "urgent_attention"]
    primary_reasons: list[str]
    component_breakdown: list[CustomerAttentionComponent]
    unresolved_conversation_count: int
    pending_conversation_count: int
    waiting_conversation_count: int
    longest_waiting_seconds: float | None = None
    oldest_unresolved_at: datetime | None = None
    negative_customer_message_count: int
    classified_sentiment_sample_size: int
    repeat_contact_count: int
    urgent_conversation_count: int
    high_priority_conversation_count: int
    last_contact_at: datetime | None = None
    data_quality: list[DataQualityNotice]


class CustomerAttentionResponse(BaseModel):
    generated_at: datetime
    applied_filters: AppliedFilters
    customers: list[CustomerAttentionItem]
    pagination: PaginationMeta
    data_quality: list[DataQualityNotice]
