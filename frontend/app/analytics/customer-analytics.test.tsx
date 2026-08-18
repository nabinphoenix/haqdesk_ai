import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CustomerAnalyticsSection from "./components/CustomerAnalyticsSection";
import type { CustomerActivityResponse, CustomerAttentionResponse, CustomerSummary, MetricValue } from "./types";

const metric = (value: number): MetricValue => ({ value, previous_value: 0, absolute_change: value, percentage_change: null, sample_size: null, status: "available", reason: null });
const filters = { from: "2026-01-01T00:00:00Z", to: "2026-01-08T00:00:00Z", timezone: "UTC", platform: null, agent_id: null, status: null, priority: null, include_deleted: false, comparison: "previous_period" as const };
const summary: CustomerSummary = { generated_at: "2026-01-08T00:00:00Z", applied_filters: filters, metrics: { active_customers: metric(2), new_customers: metric(1), returning_customers: metric(1), customers_with_open_conversations: metric(1), customers_waiting_for_reply: metric(1), customers_needing_attention: metric(1), customers_with_urgent_attention: metric(0), repeat_contact_customers: metric(1), average_conversations_per_customer: metric(1.5), average_messages_per_customer: metric(4) }, data_quality: [] };
const active: CustomerActivityResponse = { generated_at: summary.generated_at, applied_filters: filters, pagination: { limit: 20, offset: 0, total: 1, has_more: false }, data_quality: [], insights: [], customers: [{ customer_id: 1, display_name: "Asha Customer", avatar_url: null, email: null, phone: null, platforms_used: ["facebook","instagram"], alias_count: 1, total_conversations: 3, total_messages: 8, customer_messages: 5, business_replies: 3, active_days: 2, first_contact_at: "2025-12-01T00:00:00Z", last_contact_at: "2026-01-07T00:00:00Z", currently_open_conversations: 2, pending_conversations: 1, resolved_conversations: 1, high_priority_conversations: 1, urgent_conversations: 0, negative_customer_messages: 2, not_yet_analyzed_customer_messages: 1, average_messages_per_conversation: 2.67, waiting_for_reply: true, conversations_waiting_for_reply: 1, longest_waiting_seconds: 7200, oldest_waiting_since: "2026-01-07T00:00:00Z", last_customer_message_at: "2026-01-07T00:00:00Z", last_business_reply_at: null, repeat_contact_count: 1, shortest_gap_seconds: 86400, average_gap_seconds: 86400, latest_repeat_contact_at: "2026-01-06T00:00:00Z", data_quality: [] }] };
const attention: CustomerAttentionResponse = { generated_at: summary.generated_at, applied_filters: filters, pagination: { limit: 20, offset: 0, total: 1, has_more: false }, data_quality: [], customers: [{ customer_id: 1, display_name: "Asha Customer", avatar_url: null, platforms_used: ["facebook","instagram"], attention_score: 62.5, attention_level: "needs_attention", primary_reasons: ["2 currently open conversations", "1 conversation is waiting for a business reply"], component_breakdown: [{ key: "waiting", label: "Waiting for reply", raw_value: 7200, normalized_value: .6, maximum_weight: 25, contribution: 15, explanation: "The longest unanswered customer message has waited 2 hours." }], unresolved_conversation_count: 2, pending_conversation_count: 1, waiting_conversation_count: 1, longest_waiting_seconds: 7200, oldest_unresolved_at: "2026-01-01T00:00:00Z", negative_customer_message_count: 2, classified_sentiment_sample_size: 4, repeat_contact_count: 1, urgent_conversation_count: 0, high_priority_conversation_count: 1, last_contact_at: "2026-01-07T00:00:00Z", data_quality: [] }] };

describe("Customer Activity analytics", () => {
  it("renders summary cards and the most active customer table", () => {
    render(<CustomerAnalyticsSection summary={summary} active={active} attention={attention} onRefresh={vi.fn()} refreshing={false} />);
    expect(screen.getByText("Customer Activity")).toBeInTheDocument();
    expect(screen.getByText("Active Customers")).toBeInTheDocument();
    expect(screen.getByText("Most Active Customers")).toBeInTheDocument();
    expect(screen.getByText("Asha Customer")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open inbox" })).toHaveAttribute("href", "/inbox");
    expect(screen.getByLabelText(/latest sent message/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/opened another conversation within seven days/i)).toBeInTheDocument();
  });

  it("renders attention levels, reasons, waits, and the details drawer", () => {
    render(<CustomerAnalyticsSection summary={summary} active={active} attention={attention} onRefresh={vi.fn()} refreshing={false} />);
    fireEvent.click(screen.getByRole("button", { name: "Customers Needing Attention" }));
    expect(screen.getByText("62.5")).toBeInTheDocument();
    expect(screen.getByText("Needs Attention")).toBeInTheDocument();
    expect(screen.getByText(/2 currently open conversations/)).toBeInTheDocument();
    expect(screen.getByText("2 hr")).toBeInTheDocument();
    fireEvent.click(within(screen.getByRole("table")).getByText("Asha Customer"));
    expect(screen.getByRole("dialog", { name: "Customer attention details" })).toBeInTheDocument();
    expect(screen.getByText("Why this customer appears here")).toBeInTheDocument();
    expect(screen.getByText("+15")).toBeInTheDocument();
  });

  it("supports search, empty results, and refresh", () => {
    const refresh = vi.fn();
    render(<CustomerAnalyticsSection summary={summary} active={active} attention={attention} onRefresh={refresh} refreshing={false} />);
    fireEvent.change(screen.getByLabelText("Search customers"), { target: { value: "missing" } });
    expect(screen.getByText("No active customers match this view.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Refresh Customers/ }));
    expect(refresh).toHaveBeenCalled();
  });
});
