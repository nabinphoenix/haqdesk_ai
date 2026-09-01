"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BarChart3, LayoutDashboard, Radio, Sparkles, UsersRound } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import AnalyticsEmptyState from "./components/AnalyticsEmptyState";
import AnalyticsErrorState from "./components/AnalyticsErrorState";
import AnalyticsFilterBar from "./components/AnalyticsFilterBar";
import FAQOpportunities from "./components/FAQOpportunities";
import AnalyticsPageHeader from "./components/AnalyticsPageHeader";
import AnalyticsSkeleton from "./components/AnalyticsSkeleton";
import DataQualityBanner from "./components/DataQualityBanner";
import { ChannelDecisionView, GrowthInsights, OperationsOverview, TeamOperationsView } from "./components/DecisionPanels";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import type { AnalyticsSummary, CustomerAttentionResponse, CustomerSummary, FAQOpportunitiesResponse, FAQOpportunity, MessageTrend, PlatformAnalytics } from "./types";

type AnalyticsRole = "business_admin" | "supervisor";
type AnalyticsView = "operations" | "channels" | "team" | "insights";

export default function AnalyticsPage() {
  return <Suspense fallback={<div className="page-padded"><AnalyticsSkeleton /></div>}><AnalyticsContent /></Suspense>;
}

function AnalyticsContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { filters, setFilter, setFilters, resetFilters, queryString } = useAnalyticsFilters();
  const [role, setRole] = useState<AnalyticsRole>("business_admin");
  const [agentOptions, setAgentOptions] = useState<{ id: number; name: string; email: string }[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trend, setTrend] = useState<MessageTrend | null>(null);
  const [platforms, setPlatforms] = useState<PlatformAnalytics | null>(null);
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null);
  const [attentionCustomers, setAttentionCustomers] = useState<CustomerAttentionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState("");
  const [error, setError] = useState("");
  const [roleReady, setRoleReady] = useState(false);
  const [faqData, setFaqData] = useState<FAQOpportunitiesResponse | null>(null);
  const [faqLoading, setFaqLoading] = useState(false);
  const [faqError, setFaqError] = useState("");
  const [faqActionFingerprint, setFaqActionFingerprint] = useState<string | null>(null);

  useEffect(() => {
    const storedRole = localStorage.getItem("userRole");
    if (storedRole === "supervisor") setRole("supervisor");
    else if (storedRole && storedRole !== "business_admin") router.replace("/inbox");
    setRoleReady(true);
  }, [router]);

  const views = useMemo(() => {
    const operationsLabel = role === "supervisor" ? "Team queue" : "Support operations";
    const result: { id: AnalyticsView; label: string; icon: typeof LayoutDashboard }[] = [
      { id: "operations", label: operationsLabel, icon: LayoutDashboard },
      { id: "channels", label: "Channels", icon: Radio },
      { id: "team", label: "Team capacity", icon: UsersRound },
    ];
    if (role === "business_admin") result.push({ id: "insights", label: "Growth insights", icon: Sparkles });
    return result;
  }, [role]);

  const requestedView = searchParams.get("view");
  const requested = requestedView === "overview" ? "operations" : requestedView;
  const activeView: AnalyticsView = views.some((view) => view.id === requested) ? requested as AnalyticsView : "operations";
  const setActiveView = (view: AnalyticsView) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", view);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

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
        // Agent filters and roster remain optional when team data is unavailable.
      });
    return () => { active = false; };
  }, []);

  const loadAnalytics = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const [summaryResponse, trendResponse, platformsResponse, customerSummaryResponse, attentionCustomersResponse] = await Promise.all([
        fetchWithAuth(`/api/v1/analytics/summary?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/message-trend?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/platforms?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/customers/summary?${queryString}`, { cache: "no-store" }),
        fetchWithAuth(`/api/v1/analytics/customers/attention?${queryString}&limit=10&offset=0&sort_by=attention_score&sort_order=desc`, { cache: "no-store" }),
      ]);
      const responses = [summaryResponse, trendResponse, platformsResponse, customerSummaryResponse, attentionCustomersResponse];
      if (responses.some((response) => !response.ok)) {
        const failed = responses.find((response) => !response.ok)!;
        const payload = await failed.json().catch(() => ({}));
        throw new Error(payload.detail || "Analytics request failed");
      }
      const [nextSummary, nextTrend, nextPlatforms, nextCustomerSummary, nextAttentionCustomers] = await Promise.all([
        summaryResponse.json() as Promise<AnalyticsSummary>,
        trendResponse.json() as Promise<MessageTrend>,
        platformsResponse.json() as Promise<PlatformAnalytics>,
        customerSummaryResponse.json() as Promise<CustomerSummary>,
        attentionCustomersResponse.json() as Promise<CustomerAttentionResponse>,
      ]);
      setSummary(nextSummary);
      setTrend(nextTrend);
      setPlatforms(nextPlatforms);
      setCustomerSummary(nextCustomerSummary);
      setAttentionCustomers(nextAttentionCustomers);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [queryString]);

  useEffect(() => { void loadAnalytics(); }, [loadAnalytics]);

  const loadFAQOpportunities = useCallback(async () => {
    setFaqLoading(true);
    setFaqError("");
    try {
      const response = await fetchWithAuth(`/api/v1/analytics/faq-opportunities?${queryString}`, { cache: "no-store" });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not analyse recurring questions.");
      }
      setFaqData(await response.json() as FAQOpportunitiesResponse);
    } catch (caught) {
      setFaqError(caught instanceof Error ? caught.message : "Could not analyse recurring questions.");
    } finally {
      setFaqLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    if (roleReady && role === "business_admin" && activeView === "insights") {
      void loadFAQOpportunities();
    }
  }, [activeView, loadFAQOpportunities, role, roleReady]);

  const createKnowledgeDraft = useCallback(async (opportunity: FAQOpportunity) => {
    setFaqActionFingerprint(opportunity.fingerprint);
    setFaqError("");
    try {
      const response = await fetchWithAuth(`/api/v1/analytics/faq-opportunities/${opportunity.fingerprint}/create-knowledge-draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: opportunity.suggested_title,
          representative_question: opportunity.representative_question,
          example_questions: opportunity.example_questions,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not create the Knowledge Base draft.");
      }
      const draft = await response.json() as { knowledge_document_id: number; status: string };
      setFaqData((current) => current ? {
        ...current,
        opportunities: current.opportunities.map((item) => item.fingerprint === opportunity.fingerprint ? {
          ...item,
          status: draft.status,
          knowledge_document_id: draft.knowledge_document_id,
        } : item),
      } : current);
    } catch (caught) {
      setFaqError(caught instanceof Error ? caught.message : "Could not create the Knowledge Base draft.");
    } finally {
      setFaqActionFingerprint(null);
    }
  }, []);

  const dismissFAQOpportunity = useCallback(async (opportunity: FAQOpportunity) => {
    setFaqActionFingerprint(opportunity.fingerprint);
    setFaqError("");
    try {
      const response = await fetchWithAuth(`/api/v1/analytics/faq-opportunities/${opportunity.fingerprint}/dismiss`, { method: "POST" });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not dismiss this opportunity.");
      }
      setFaqData((current) => current ? {
        ...current,
        opportunities: current.opportunities.filter((item) => item.fingerprint !== opportunity.fingerprint),
      } : current);
    } catch (caught) {
      setFaqError(caught instanceof Error ? caught.message : "Could not dismiss this opportunity.");
    } finally {
      setFaqActionFingerprint(null);
    }
  }, []);

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
      <div className="page-body custom-scrollbar space-y-6">
        <AnalyticsFilterBar filters={filters} setFilter={setFilter} setFilters={setFilters} onReset={resetFilters} agentOptions={agentOptions} />
        <nav aria-label="Analytics sections" className="overflow-x-auto pb-1"><div className="flex min-w-max gap-1 rounded-2xl border border-surface-border bg-surface-wash p-1.5">
          {views.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setActiveView(id)} aria-current={activeView === id ? "page" : undefined} className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${activeView === id ? "bg-surface text-foreground shadow-sm" : "text-muted-foreground hover:bg-surface hover:text-foreground"}`}><Icon size={15} />{label}</button>)}
        </div></nav>
        {loading && !summary ? <AnalyticsSkeleton /> : error ? <AnalyticsErrorState message={error} onRetry={() => void loadAnalytics(true)} /> : summary && trend && platforms && customerSummary && attentionCustomers ? <>
          {isEmpty ? <AnalyticsEmptyState /> : <>
            {summary.data_quality_notices.length > 0 && <DataQualityBanner notices={summary.data_quality_notices} />}
            {activeView === "operations" && <OperationsOverview summary={summary} trend={trend} platforms={platforms} customerSummary={customerSummary} attention={attentionCustomers} role={role} />}
            {activeView === "channels" && <ChannelDecisionView platforms={platforms} />}
            {activeView === "team" && <TeamOperationsView summary={summary} platforms={platforms} agentOptions={agentOptions} />}
            {activeView === "insights" && role === "business_admin" && <div className="space-y-6"><GrowthInsights summary={summary} platforms={platforms} customerSummary={customerSummary} /><FAQOpportunities data={faqData} loading={faqLoading} error={faqError} actionFingerprint={faqActionFingerprint} onRetry={() => void loadFAQOpportunities()} onCreateDraft={(opportunity) => void createKnowledgeDraft(opportunity)} onDismiss={(opportunity) => void dismissFAQOpportunity(opportunity)} /></div>}
          </>}
        </> : null}
      </div>
    </div>
  </div>;
}