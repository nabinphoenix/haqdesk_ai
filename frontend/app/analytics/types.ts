export type MetricStatus = "available" | "partial" | "unavailable";

export interface MetricValue {
  value: number | null;
  previous_value: number | null;
  absolute_change: number | null;
  percentage_change: number | null;
  sample_size: number | null;
  status: MetricStatus;
  reason: string | null;
}

export interface AppliedFilters {
  from: string;
  to: string;
  timezone: string;
  platform: string | null;
  agent_id: number | null;
  status: string | null;
  priority: string | null;
  include_deleted: boolean;
  comparison: "none" | "previous_period";
}

export interface DataQualityNotice {
  metric: string;
  severity: "info" | "warning";
  message: string;
}

export interface AnalyticsSummary {
  generated_at: string;
  applied_filters: AppliedFilters;
  metrics: {
    total_conversations: MetricValue;
    total_messages: MetricValue;
    customer_messages: MetricValue;
    agent_messages: MetricValue;
    open_conversations: MetricValue;
    pending_conversations: MetricValue;
    resolved_conversations: MetricValue;
    total_customers: MetricValue;
    knowledge_documents: MetricValue;
    knowledge_chunks: MetricValue;
    team_members: MetricValue;
    retained_ai_drafts: MetricValue;
  };
  platform_conversation_distribution: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  data_quality_notices: DataQualityNotice[];
}

export interface TimeBucket {
  start: string;
  end: string;
  label: string;
  value: number;
}

export interface MessageSeries {
  key: "all_messages" | "customer_messages" | "agent_messages";
  label: string;
  total: number;
  points: TimeBucket[];
}

export interface MessageTrend {
  generated_at: string;
  applied_filters: AppliedFilters;
  bucket: "hour" | "day" | "week" | "month";
  series: MessageSeries[];
}

export interface PlatformAnalyticsItem {
  platform: string;
  display_name: string;
  is_connected: boolean;
  conversations: MetricValue;
  messages: MetricValue;
  inbound_messages: MetricValue;
  outgoing_messages: MetricValue;
  unique_customers: MetricValue;
  conversation_share_percentage: MetricValue;
  message_share_percentage: MetricValue;
  customer_share_percentage: MetricValue;
  open_conversations: MetricValue;
  pending_conversations: MetricValue;
  resolved_conversations: MetricValue;
  unassigned_conversations: MetricValue;
  high_priority_conversations: MetricValue;
  urgent_priority_conversations: MetricValue;
  positive_messages: MetricValue;
  neutral_messages: MetricValue;
  negative_messages: MetricValue;
  unclassified_messages: MetricValue;
  negative_sentiment_rate: MetricValue;
  classified_sentiment_sample_size: number;
  average_first_response_seconds: MetricValue;
  median_first_response_seconds: MetricValue;
  p90_first_response_seconds: MetricValue;
  response_sample_size: number;
  unanswered_conversations: MetricValue;
  peak_weekday: string | null;
  peak_hour: number | null;
  peak_hour_message_count: number;
  peak_hour_conversation_count: number;
  data_quality: DataQualityNotice[];
}

export interface PlatformAnalytics {
  generated_at: string;
  applied_filters: AppliedFilters;
  platforms: PlatformAnalyticsItem[];
  data_quality: DataQualityNotice[];
  insights: string[];
}

export interface CustomerSummary {
  generated_at: string;
  applied_filters: AppliedFilters;
  metrics: Record<"active_customers" | "new_customers" | "returning_customers" | "customers_with_open_conversations" | "customers_waiting_for_reply" | "customers_needing_attention" | "customers_with_urgent_attention" | "repeat_contact_customers" | "average_conversations_per_customer" | "average_messages_per_customer", MetricValue>;
  data_quality: DataQualityNotice[];
}

export interface Pagination { limit: number; offset: number; total: number; has_more: boolean; }
export interface CustomerActivityItem {
  customer_id: number; display_name: string; avatar_url: string | null; email: string | null; phone: string | null;
  platforms_used: string[]; alias_count: number; total_conversations: number; total_messages: number;
  customer_messages: number; business_replies: number; active_days: number; first_contact_at: string | null; last_contact_at: string | null;
  currently_open_conversations: number; pending_conversations: number; resolved_conversations: number;
  high_priority_conversations: number; urgent_conversations: number; negative_customer_messages: number;
  not_yet_analyzed_customer_messages: number; average_messages_per_conversation: number; waiting_for_reply: boolean;
  conversations_waiting_for_reply: number; longest_waiting_seconds: number | null; oldest_waiting_since: string | null;
  last_customer_message_at: string | null; last_business_reply_at: string | null; repeat_contact_count: number;
  shortest_gap_seconds: number | null; average_gap_seconds: number | null; latest_repeat_contact_at: string | null;
  data_quality: DataQualityNotice[];
}
export interface CustomerActivityResponse { generated_at: string; applied_filters: AppliedFilters; customers: CustomerActivityItem[]; pagination: Pagination; data_quality: DataQualityNotice[]; insights: string[]; }
export interface AttentionComponent { key: string; label: string; raw_value: number; normalized_value: number; maximum_weight: number; contribution: number; explanation: string; }
export interface CustomerAttentionItem {
  customer_id: number; display_name: string; avatar_url: string | null; platforms_used: string[]; attention_score: number;
  attention_level: "normal" | "watch" | "needs_attention" | "urgent_attention"; primary_reasons: string[];
  component_breakdown: AttentionComponent[]; unresolved_conversation_count: number; pending_conversation_count: number;
  waiting_conversation_count: number; longest_waiting_seconds: number | null; oldest_unresolved_at: string | null;
  negative_customer_message_count: number; classified_sentiment_sample_size: number; repeat_contact_count: number;
  urgent_conversation_count: number; high_priority_conversation_count: number; last_contact_at: string | null; data_quality: DataQualityNotice[];
}
export interface CustomerAttentionResponse { generated_at: string; applied_filters: AppliedFilters; customers: CustomerAttentionItem[]; pagination: Pagination; data_quality: DataQualityNotice[]; }

export interface AnalyticsFilterState {
  from: string;
  to: string;
  timezone: string;
  platform: string;
  agent_id: string;
  status: string;
  priority: string;
  include_deleted: boolean;
  comparison: "none" | "previous_period";
}

export interface FAQOpportunity {
  fingerprint: string;
  suggested_title: string;
  representative_question: string;
  example_questions: string[];
  occurrence_count: number;
  unique_customer_count: number;
  channels: Record<string, number>;
  last_asked_at: string | null;
  status: "active" | "dismissed" | "draft_created" | string;
  knowledge_document_id: number | null;
}

export interface FAQOpportunitiesResponse {
  generated_at: string;
  analysis_method: "semantic_embeddings" | "text_similarity_fallback" | string;
  messages_scanned: number;
  question_candidates: number;
  minimum_occurrences: number;
  minimum_unique_customers: number;
  opportunities: FAQOpportunity[];
  privacy_note: string;
}