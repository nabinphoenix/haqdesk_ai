import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import PlatformAnalyticsSection, { formatDuration, formatPeakTime } from "./components/PlatformAnalyticsSection";
import type { MetricValue, PlatformAnalytics, PlatformAnalyticsItem } from "./types";

const TYPICAL_TOOLTIP = "The middle response time. Half of responses were faster and half were slower.";
const NINETY_TOOLTIP = "90% of customer conversations received a first response within this time. The slowest 10% took longer.";

const metric = (value: number | null, status: MetricValue["status"] = "available", sampleSize: number | null = null): MetricValue => ({
  value, previous_value: 0, absolute_change: value, percentage_change: null,
  sample_size: sampleSize, status, reason: status === "available" ? null : "Stored metadata is partial.",
});

function platform(platform: "facebook" | "instagram", conversations: number, connected: boolean): PlatformAnalyticsItem {
  return {
    platform, display_name: platform === "facebook" ? "Facebook" : "Instagram", is_connected: connected,
    conversations: metric(conversations), messages: metric(conversations * 3), inbound_messages: metric(conversations * 2), outgoing_messages: metric(conversations), unique_customers: metric(conversations),
    conversation_share_percentage: metric(platform === "facebook" ? 40 : 60), message_share_percentage: metric(50), customer_share_percentage: metric(50),
    open_conversations: metric(platform === "facebook" ? 4 : 1, "unavailable"), pending_conversations: metric(1, "unavailable"), resolved_conversations: metric(2, "unavailable"), unassigned_conversations: metric(1, "unavailable"), high_priority_conversations: metric(0, "unavailable"), urgent_priority_conversations: metric(0, "unavailable"),
    positive_messages: metric(2), neutral_messages: metric(1), negative_messages: metric(platform === "facebook" ? 2 : 0), unclassified_messages: metric(3), negative_sentiment_rate: metric(platform === "facebook" ? 40 : 0), classified_sentiment_sample_size: 5,
    average_first_response_seconds: metric(90, "partial", 2), median_first_response_seconds: metric(platform === "facebook" ? 72 : 360, "partial", 2), p90_first_response_seconds: metric(4320, "partial", 2), response_sample_size: 2, unanswered_conversations: metric(1),
    peak_weekday: "monday", peak_hour: 19, peak_hour_message_count: 3, peak_hour_conversation_count: 1,
    data_quality: [],
  };
}

const data: PlatformAnalytics = {
  generated_at: "2026-01-03T00:00:00Z",
  applied_filters: { from: "2026-01-01T00:00:00Z", to: "2026-01-03T00:00:00Z", timezone: "UTC", platform: null, agent_id: null, status: null, priority: null, include_deleted: false, comparison: "previous_period" },
  platforms: [platform("facebook", 2, true), platform("instagram", 5, false)],
  data_quality: [{ metric: "first_response", severity: "warning", message: "Stored response metadata is partial." }],
  insights: ["Instagram received the highest number of conversations in the selected period."],
};

describe("Platform Analytics", () => {
  it("renders Facebook, Instagram, connection state, zero values, sentiment, and notices", () => {
    render(<PlatformAnalyticsSection data={data} filteredPlatform="" />);
    expect(screen.getAllByText("Facebook").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Instagram").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Connected").length).toBeGreaterThan(0);
    expect(screen.getByText("Past activity only")).toBeInTheDocument();
    expect(screen.getByText("Customer Sentiment")).toBeInTheDocument();
    expect(screen.getAllByText("Not Yet Analyzed").length).toBeGreaterThan(0);
    expect(screen.getByText("Stored response metadata is limited.")).toBeInTheDocument();
    expect(screen.getAllByText("0 negative messages — 0% of analyzed customer messages").length).toBeGreaterThan(0);
  });

  it("formats response durations for seconds, minutes, and hours", () => {
    expect(formatDuration(42)).toBe("42 sec");
    expect(formatDuration(360)).toBe("6 min");
    expect(formatDuration(4320)).toBe("1 hr 12 min");
    expect(formatDuration(null)).toBe("Not Available Yet");
  });

  it("sorts the platform performance table", () => {
    render(<PlatformAnalyticsSection data={data} filteredPlatform="" />);
    const table = screen.getByRole("table");
    let rows = within(table).getAllByRole("row");
    expect(within(rows[1]).getByText("Instagram")).toBeInTheDocument();
    fireEvent.click(within(table).getByRole("button", { name: /platform/i }));
    rows = within(table).getAllByRole("row");
    expect(within(rows[1]).getByText("Instagram")).toBeInTheDocument();
    fireEvent.click(within(table).getByRole("button", { name: /platform/i }));
    rows = within(table).getAllByRole("row");
    expect(within(rows[1]).getByText("Facebook")).toBeInTheDocument();
  });

  it("explains when a global platform filter hides comparisons", () => {
    const filtered = { ...data, platforms: [data.platforms[0]] };
    render(<PlatformAnalyticsSection data={filtered} filteredPlatform="facebook" />);
    expect(screen.getByText(/Filtered to facebook; other channels are intentionally hidden/i)).toBeInTheDocument();
    expect(screen.queryByText("Instagram")).not.toBeInTheDocument();
  });

  it("uses business-friendly response, sentiment, and date language", () => {
    render(<PlatformAnalyticsSection data={data} filteredPlatform="" />);
    expect(screen.queryByText(/P90/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/90% Responded Within/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Typical Response Time/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("2 negative messages — 40% of analyzed customer messages").length).toBeGreaterThan(0);
    expect(screen.queryByText("4320")).not.toBeInTheDocument();
    expect(screen.getAllByText("1 hr 12 min").length).toBeGreaterThan(0);
    expect(screen.getByText(/New conversations are counted using the conversation creation date/)).toBeInTheDocument();
    expect(screen.getAllByLabelText(TYPICAL_TOOLTIP).length).toBeGreaterThan(0);
    expect(screen.getAllByLabelText(NINETY_TOOLTIP).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Based on 2 answered conversations").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Limited Data").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Monday at 7:00 PM").length).toBeGreaterThan(0);
    expect(screen.getByText("Times shown in UTC.")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByRole("button", { name: /^Customer Messages/i })).toBeInTheDocument();
    expect(within(table).getByRole("button", { name: /^Business Replies/i })).toBeInTheDocument();
  });

  it("uses singular sample wording and hides zero-sample durations", () => {
    const single = platform("facebook", 1, true);
    single.median_first_response_seconds = metric(41.18, "partial", 1);
    single.p90_first_response_seconds = metric(41.18, "partial", 1);
    render(<PlatformAnalyticsSection data={{ ...data, platforms: [single] }} filteredPlatform="" />);
    expect(screen.getAllByText("Based on 1 answered conversation").length).toBeGreaterThan(0);
    expect(screen.getAllByText("41 sec").length).toBeGreaterThan(0);
  });

  it("shows Not Available Yet instead of 0 sec when no conversations were answered", () => {
    const unanswered = platform("instagram", 0, false);
    unanswered.median_first_response_seconds = metric(null, "partial", 0);
    unanswered.p90_first_response_seconds = metric(null, "partial", 0);
    render(<PlatformAnalyticsSection data={{ ...data, platforms: [unanswered] }} filteredPlatform="" />);
    expect(screen.getAllByText("Not Available Yet").length).toBeGreaterThan(0);
    expect(screen.queryByText("0 sec")).not.toBeInTheDocument();
  });

  it("formats busiest times in business language", () => {
    expect(formatPeakTime("tuesday", 16)).toBe("Tuesday at 4:00 PM");
    expect(formatPeakTime(null, null)).toBe("Not Available Yet");
  });
});
