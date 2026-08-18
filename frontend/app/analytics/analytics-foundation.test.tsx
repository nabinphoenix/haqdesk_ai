import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AnalyticsPage from "./page";
import AnalyticsFilterBar from "./components/AnalyticsFilterBar";
import DataQualityBanner from "./components/DataQualityBanner";
import KpiGrid from "./components/KpiGrid";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import type { AnalyticsFilterState, AnalyticsSummary, CustomerActivityResponse, CustomerAttentionResponse, CustomerSummary, MessageTrend, PlatformAnalytics } from "./types";
import { fetchWithAuth } from "@/lib/api";

const replace = vi.fn();
let urlParams = new URLSearchParams("from=2026-01-01T00%3A00%3A00.000Z&to=2026-01-03T00%3A00%3A00.000Z&timezone=UTC&comparison=previous_period");

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/analytics",
  useSearchParams: () => urlParams,
}));
vi.mock("@/lib/api", () => ({ fetchWithAuth: vi.fn() }));

const metric = (value: number, status: "available" | "partial" | "unavailable" = "available") => ({
  value, previous_value: 0, absolute_change: value, percentage_change: null,
  sample_size: null, status, reason: status === "available" ? null : "Limited historical data",
});

const summary: AnalyticsSummary = {
  generated_at: "2026-01-03T00:00:00Z",
  applied_filters: { from: "2026-01-01T00:00:00Z", to: "2026-01-03T00:00:00Z", timezone: "UTC", platform: null, agent_id: null, status: null, priority: null, include_deleted: false, comparison: "previous_period" },
  metrics: {
    total_conversations: metric(2), total_messages: metric(3), customer_messages: metric(2), agent_messages: metric(1),
    open_conversations: metric(1, "partial"), pending_conversations: metric(1, "partial"), resolved_conversations: metric(0, "partial"),
    total_customers: metric(2), knowledge_documents: metric(0), knowledge_chunks: metric(0), team_members: metric(3, "unavailable"), retained_ai_drafts: metric(0, "partial"),
  },
  platform_conversation_distribution: { facebook: 1, instagram: 1 },
  sentiment_distribution: { negative: 1, positive: 1 },
  data_quality_notices: [{ metric: "retained_ai_drafts", severity: "warning", message: "Draft history is partial." }],
};

const trend: MessageTrend = {
  generated_at: summary.generated_at, applied_filters: summary.applied_filters, bucket: "day",
  series: ["all_messages", "customer_messages", "agent_messages"].map((key, index) => ({
    key: key as "all_messages" | "customer_messages" | "agent_messages",
    label: key, total: index === 0 ? 3 : 1,
    points: [{ start: "2026-01-01T00:00:00Z", end: "2026-01-02T00:00:00Z", label: "Jan 1", value: index === 0 ? 3 : 1 }],
  })),
};
const platformAnalytics: PlatformAnalytics = {
  generated_at: summary.generated_at, applied_filters: summary.applied_filters,
  platforms: [], data_quality: [], insights: [],
};
const customerSummary: CustomerSummary = {
  generated_at: summary.generated_at, applied_filters: summary.applied_filters, data_quality: [],
  metrics: { active_customers: metric(0), new_customers: metric(0), returning_customers: metric(0), customers_with_open_conversations: metric(0), customers_waiting_for_reply: metric(0), customers_needing_attention: metric(0), customers_with_urgent_attention: metric(0), repeat_contact_customers: metric(0), average_conversations_per_customer: metric(0), average_messages_per_customer: metric(0) },
};
const activeCustomers: CustomerActivityResponse = { generated_at: summary.generated_at, applied_filters: summary.applied_filters, customers: [], pagination: { limit: 20, offset: 0, total: 0, has_more: false }, data_quality: [], insights: [] };
const attentionCustomers: CustomerAttentionResponse = { generated_at: summary.generated_at, applied_filters: summary.applied_filters, customers: [], pagination: { limit: 20, offset: 0, total: 0, has_more: false }, data_quality: [] };

function response(body: unknown, ok = true) {
  return Promise.resolve({ ok, json: () => Promise.resolve(body) } as Response);
}
function dashboardResponse(endpoint: string, summaryValue: AnalyticsSummary = summary): Promise<Response> {
  if (endpoint.includes("customers/summary")) return response(customerSummary);
  if (endpoint.includes("customers/active")) return response(activeCustomers);
  if (endpoint.includes("customers/attention")) return response(attentionCustomers);
  if (endpoint.includes("message-trend")) return response(trend);
  if (endpoint.includes("/platforms")) return response(platformAnalytics);
  return response(summaryValue);
}

beforeEach(() => {
  vi.clearAllMocks();
  urlParams = new URLSearchParams("from=2026-01-01T00%3A00%3A00.000Z&to=2026-01-03T00%3A00%3A00.000Z&timezone=UTC&comparison=previous_period");
});

describe("analytics page states", () => {
  it("shows loading and then renders zero-valued KPIs and notices", async () => {
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => dashboardResponse(String(endpoint)));
    render(<AnalyticsPage />);
    expect(screen.getByLabelText("Loading analytics")).toBeInTheDocument();
    expect(await screen.findByText(/Pending AI Reply Suggestions/)).toBeInTheDocument();
    expect(screen.getByLabelText("AI suggestions currently saved and waiting for review. This is not the total number of AI suggestions ever generated.")).toBeInTheDocument();
    expect(screen.getByText("Draft history is limited.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Overview" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: "Channels" })).toBeInTheDocument();
    expect(screen.queryByText("Customer Sentiment")).not.toBeInTheDocument();
    expect(screen.queryByText("By Platform")).not.toBeInTheDocument();
    expect(screen.queryByText(/Agent messages/i)).not.toBeInTheDocument();
    expect(screen.getByText("Business Replies")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Previous 2 days/ })).toBeInTheDocument();
  });

  it("renders dense channel analytics only in the URL-selected Channels tab", async () => {
    urlParams.set("view", "channels");
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => dashboardResponse(String(endpoint)));
    render(<AnalyticsPage />);
    expect(await screen.findByText("Channel Performance")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Channels" })).toHaveAttribute("aria-current", "page");
    expect(screen.getAllByText("Customer Sentiment").length).toBeGreaterThan(0);
    expect(screen.queryByText("Current Support Status")).not.toBeInTheDocument();
  });

  it("shows an error state", async () => {
    vi.mocked(fetchWithAuth).mockRejectedValue(new Error("Backend unavailable"));
    render(<AnalyticsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Backend unavailable");
  });

  it("shows an empty state", async () => {
    const empty = { ...summary, metrics: { ...summary.metrics, total_conversations: metric(0), total_messages: metric(0) } };
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => dashboardResponse(String(endpoint), empty));
    render(<AnalyticsPage />);
    expect(await screen.findByText("No analytics data for these filters")).toBeInTheDocument();
  });

  it("refreshes both analytics requests", async () => {
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => dashboardResponse(String(endpoint)));
    render(<AnalyticsPage />);
    await screen.findByText("Total Conversations");
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(fetchWithAuth).toHaveBeenCalledTimes(13));
  });

  it("exports a CSV report with the active filters", async () => {
    const createObjectURL = vi.fn(() => "blob:analytics");
    const revokeObjectURL = vi.fn();
    Object.defineProperties(URL, {
      createObjectURL: { value: createObjectURL, configurable: true },
      revokeObjectURL: { value: revokeObjectURL, configurable: true },
    });
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => String(endpoint).includes("/export?") ? Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(["report"])),
        headers: new Headers({ "Content-Disposition": 'attachment; filename="filtered-report.csv"' }),
      } as Response) : dashboardResponse(String(endpoint)));
    render(<AnalyticsPage />);
    await screen.findByText("Total Conversations");
    fireEvent.click(screen.getByRole("button", { name: /export csv/i }));
    await waitFor(() => expect(fetchWithAuth).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/v1/analytics/export?from="),
      { cache: "no-store" },
    ));
    await waitFor(() => expect(createObjectURL).toHaveBeenCalled());
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:analytics");
  });

  it("offers a PDF export using the active filters", async () => {
    Object.defineProperties(URL, {
      createObjectURL: { value: vi.fn(() => "blob:pdf"), configurable: true },
      revokeObjectURL: { value: vi.fn(), configurable: true },
    });
    vi.mocked(fetchWithAuth).mockImplementation((endpoint) => String(endpoint).includes("/export?") ? Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(["%PDF"])),
        headers: new Headers({ "Content-Disposition": 'attachment; filename="filtered-report.pdf"' }),
      } as Response) : dashboardResponse(String(endpoint)));
    render(<AnalyticsPage />);
    await screen.findByText("Total Conversations");
    fireEvent.click(screen.getByRole("button", { name: /export pdf/i }));
    await waitFor(() => expect(fetchWithAuth).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/analytics\/export\?.*format=pdf/),
      { cache: "no-store" },
    ));
  });
});

describe("filters and reusable components", () => {
  const filters: AnalyticsFilterState = { from: "2026-01-01T00:00:00Z", to: "2026-01-03T00:00:00Z", timezone: "UTC", platform: "", agent_id: "", status: "", priority: "", include_deleted: false, comparison: "previous_period" };

  it("emits filter changes and reset", () => {
    const setFilter = vi.fn(); const reset = vi.fn();
    render(<AnalyticsFilterBar filters={filters} setFilter={setFilter} onReset={reset} agentOptions={[{ id: 7, name: "Sita Sharma", email: "sita@example.com" }]} />);
    fireEvent.change(screen.getByLabelText("Platform"), { target: { value: "facebook" } });
    fireEvent.change(screen.getByLabelText("Agent"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(setFilter).toHaveBeenCalledWith("platform", "facebook");
    expect(setFilter).toHaveBeenCalledWith("agent_id", "7");
    expect(screen.getByRole("option", { name: "Sita Sharma" })).toBeInTheDocument();
    expect(reset).toHaveBeenCalled();
  });

  it("renders KPIs including zero and partial/unavailable notices", () => {
    render(<><KpiGrid summary={summary} /><DataQualityBanner notices={summary.data_quality_notices} /></>);
    expect(screen.getByText(/Pending AI Reply Suggestions/)).toBeInTheDocument();
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
    expect(screen.getByText("Draft history is limited.")).toBeInTheDocument();
  });

  it("synchronizes filter changes to the URL", () => {
    function Harness() { const value = useAnalyticsFilters(); return <button onClick={() => value.setFilter("platform", "facebook")}>Set platform</button>; }
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Set platform" }));
    expect(replace).toHaveBeenCalledWith(expect.stringContaining("platform=facebook"), { scroll: false });
  });
});
