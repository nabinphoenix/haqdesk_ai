"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BarChart3, LayoutDashboard, Radio, Users } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import AnalyticsEmptyState from "./components/AnalyticsEmptyState";
import AnalyticsErrorState from "./components/AnalyticsErrorState";
import AnalyticsFilterBar from "./components/AnalyticsFilterBar";
import AnalyticsPageHeader from "./components/AnalyticsPageHeader";
import AnalyticsSkeleton from "./components/AnalyticsSkeleton";
import DataQualityBanner from "./components/DataQualityBanner";
import KpiGrid from "./components/KpiGrid";
import MessageVolumeChart from "./components/MessageVolumeChart";
import PlatformAnalyticsSection from "./components/PlatformAnalyticsSection";
import CustomerAnalyticsSection from "./components/CustomerAnalyticsSection";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import type { AnalyticsSummary, CustomerActivityResponse, CustomerAttentionResponse, CustomerSummary, MessageTrend, PlatformAnalytics } from "./types";

export default function AnalyticsPage() {
  return <Suspense fallback={<div className="page-padded"><AnalyticsSkeleton /></div>}><AnalyticsContent /></Suspense>;
}

function AnalyticsContent() {
  type AnalyticsView = "overview" | "channels" | "customers" | "trends";
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const requestedView = searchParams.get("view");
  const activeView: AnalyticsView = ["overview", "channels", "customers", "trends"].includes(requestedView || "") ? requestedView as AnalyticsView : "overview";
  const setActiveView = (view: AnalyticsView) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", view);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };
  const { filters, setFilter, resetFilters, queryString } = useAnalyticsFilters();
  const [agentOptions, setAgentOptions] = useState<{ id: number; name: string; email: string }[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trend, setTrend] = useState<MessageTrend | null>(null);
  const [platforms, setPlatforms] = useState<PlatformAnalytics | null>(null);
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null);
  const [activeCustomers, setActiveCustomers] = useState<CustomerActivityResponse | null>(null);
  const [attentionCustomers, setAttentionCustomers] = useState<CustomerAttentionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void fetchWithAuth("/api/v1/team/members", { cache: "no-store" })
      .then(async (response) => response.ok ? response.json() : [])
      .then((members: unknown) => {
        if (active && Array.isArray(members)) {
          setAgentOptions(members.filter((member): member is { id: number; name: string; email: string } =>
            typeof member?.id === "number" && typeof member?.email === "string"
          ));
        }
      })
      .catch(() => {
        // Analytics remains usable if the optional agent-name list cannot load.
      });
    return () => { active = false; };
  }, []);

  const loadAnalytics = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const [summaryResponse, trendResponse, platformsResponse, customerSummaryResponse, activeCustomersResponse, attentionCustomersResponse] = await Promise.all([
        fetchWithAuth(`/api/v1/analytics/summary?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/message-trend?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/platforms?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/customers/summary?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/customers/active?${queryString}&limit=100&offset=0&sort_by=total_messages&sort_order=desc`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/customers/attention?${queryString}&limit=100&offset=0&sort_by=attention_score&sort_order=desc`, { cache: "no-store" }),
      ]);
      if (!summaryResponse.ok || !trendResponse.ok || !platformsResponse.ok || !customerSummaryResponse.ok || !activeCustomersResponse.ok || !attentionCustomersResponse.ok) {
        const failed = [summaryResponse, trendResponse, platformsResponse, customerSummaryResponse, activeCustomersResponse, attentionCustomersResponse].find((response) => !response.ok)!;
        const payload = await failed.json().catch(() => ({}));
        throw new Error(payload.detail || "Analytics request failed");
      }
      const [nextSummary, nextTrend, nextPlatforms, nextCustomerSummary, nextActiveCustomers, nextAttentionCustomers] = await Promise.all([
        summaryResponse.json() as Promise<AnalyticsSummary>,
        trendResponse.json() as Promise<MessageTrend>,
        platformsResponse.json() as Promise<PlatformAnalytics>,
        customerSummaryResponse.json() as Promise<CustomerSummary>,
        activeCustomersResponse.json() as Promise<CustomerActivityResponse>,
        attentionCustomersResponse.json() as Promise<CustomerAttentionResponse>,
      ]);
      setSummary(nextSummary);
      setTrend(nextTrend);
      setPlatforms(nextPlatforms);
      setCustomerSummary(nextCustomerSummary);
      setActiveCustomers(nextActiveCustomers);
      setAttentionCustomers(nextAttentionCustomers);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [queryString]);

  useEffect(() => { void loadAnalytics(); }, [loadAnalytics]);

  const exportReport = useCallback(async (format: "csv" | "pdf") => {
    setExporting(format);
    setExportError("");
    try {
      const response = await fetchWithAuth(`/api/v1/analytics/export?${queryString}&format=${format}`, { cache: "no-store" });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Analytics export failed");
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `haqdesk-analytics.${format}`;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setExportError(caught instanceof Error ? caught.message : "Could not export analytics.");
    } finally {
      setExporting(null);
    }
  }, [queryString]);

  const isEmpty = Boolean(summary && summary.metrics.total_conversations.value === 0 && summary.metrics.total_messages.value === 0);

  return <div className="page-padded font-body">
    <div className="page-shell">
      <AnalyticsPageHeader generatedAt={summary?.generated_at} refreshing={refreshing} exporting={exporting} exportDisabled={!summary || Boolean(error)} exportError={exportError} onRefresh={() => void loadAnalytics(true)} onExport={(format) => void exportReport(format)} />
      <div className="page-body custom-scrollbar space-y-7">
        <AnalyticsFilterBar filters={filters} setFilter={setFilter} onReset={resetFilters} agentOptions={agentOptions} />
        <nav aria-label="Analytics sections" className="-mx-1 overflow-x-auto px-1 pb-1"><div className="flex min-w-max gap-1 rounded-2xl border border-border bg-surface-wash p-1.5">
          {([["overview", "Overview", LayoutDashboard], ["channels", "Channels", Radio], ["customers", "Customers", Users], ["trends", "Trends", BarChart3]] as const).map(([id, label, Icon]) => <button key={id} type="button" onClick={() => setActiveView(id)} aria-current={activeView === id ? "page" : undefined} className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${activeView === id ? "bg-surface text-foreground shadow-sm" : "text-muted-foreground hover:bg-surface hover:text-foreground"}`}><Icon size={15} />{label}</button>)}
        </div></nav>
        {loading && !summary ? <AnalyticsSkeleton /> : error ? <AnalyticsErrorState message={error} onRetry={() => void loadAnalytics(true)} /> : summary && trend && platforms && customerSummary && activeCustomers && attentionCustomers ? <>
          {isEmpty ? <AnalyticsEmptyState /> : <>
            {activeView === "overview" && <div className="space-y-7"><DataQualityBanner notices={summary.data_quality_notices} /><KpiGrid summary={summary} /><section className="rounded-[2rem] border border-border bg-surface p-6"><div className="mb-5"><h2 className="text-xl font-bold">Current Support Status</h2><p className="mt-1 text-sm text-muted-foreground">A current snapshot of workload and support resources.</p></div><div className="grid grid-cols-1 gap-4 sm:grid-cols-3">{[["Pending", summary.metrics.pending_conversations.value], ["Resolved", summary.metrics.resolved_conversations.value], ["Knowledge Documents", summary.metrics.knowledge_documents.value]].map(([label, value]) => <div key={label} className="rounded-2xl bg-surface-wash p-4"><p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{label}</p><p className="mt-1 font-heading text-3xl font-black">{value?.toLocaleString() ?? "—"}</p></div>)}</div></section></div>}
            {activeView === "channels" && <PlatformAnalyticsSection data={platforms} filteredPlatform={filters.platform} />}
            {activeView === "customers" && <CustomerAnalyticsSection summary={customerSummary} active={activeCustomers} attention={attentionCustomers} refreshing={refreshing} onRefresh={() => void loadAnalytics(true)} />}
            {activeView === "trends" && <div className="space-y-5"><div><h2 className="text-2xl font-black">Message Activity</h2><p className="mt-1 text-sm text-muted-foreground">Compare customer demand and business replies over the selected period.</p></div><MessageVolumeChart trend={trend} /></div>}
          </>}
        </> : null}
      </div>
    </div>
  </div>;
}