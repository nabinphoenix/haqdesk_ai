import type { AnalyticsFilterState, MetricValue } from "./types";

export const DEFAULT_TIMEZONE = "Asia/Kathmandu";

export function defaultAnalyticsFilters(now = new Date()): AnalyticsFilterState {
  const end = new Date(now);
  const start = new Date(now);
  start.setUTCDate(start.getUTCDate() - 30);
  return {
    from: start.toISOString(),
    to: end.toISOString(),
    timezone: DEFAULT_TIMEZONE,
    platform: "",
    agent_id: "",
    status: "",
    priority: "",
    include_deleted: false,
    comparison: "previous_period",
  };
}

export function filtersToSearchParams(filters: AnalyticsFilterState): URLSearchParams {
  const params = new URLSearchParams();
  params.set("from", filters.from);
  params.set("to", filters.to);
  params.set("timezone", filters.timezone);
  if (filters.platform) params.set("platform", filters.platform);
  if (filters.agent_id) params.set("agent_id", filters.agent_id);
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.include_deleted) params.set("include_deleted", "true");
  params.set("comparison", filters.comparison);
  return params;
}

export function filtersFromSearchParams(
  params: URLSearchParams,
  defaults: AnalyticsFilterState,
): AnalyticsFilterState {
  return {
    from: params.get("from") || defaults.from,
    to: params.get("to") || defaults.to,
    timezone: params.get("timezone") || defaults.timezone,
    platform: params.get("platform") || "",
    agent_id: params.get("agent_id") || "",
    status: params.get("status") || "",
    priority: params.get("priority") || "",
    include_deleted: params.get("include_deleted") === "true",
    comparison: params.get("comparison") === "none" ? "none" : "previous_period",
  };
}

export function formatMetric(metric: MetricValue): string {
  if (metric.value === null) return "—";
  return metric.value.toLocaleString();
}

export function metricDelta(metric: MetricValue, comparisonLabel = "compared with the previous period"): string | null {
  if (metric.status === "unavailable" || metric.percentage_change === null) return null;
  const prefix = metric.percentage_change > 0 ? "+" : "";
  return `${prefix}${metric.percentage_change}% ${comparisonLabel}`;
}
