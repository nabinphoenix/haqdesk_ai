"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Clock3, Inbox, RefreshCw, ShieldAlert, UsersRound } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import type { AnalyticsSummary, CustomerAttentionResponse, CustomerSummary, MetricValue, PlatformAnalytics } from "../analytics/types";

type TeamMember = { id: number; name?: string; email?: string; role?: string; status?: string };
type Conversation = { id: number; customer_name?: string; last_message?: string; priority?: string; unread?: number; status?: string; platform?: string };

const metricValue = (metric?: MetricValue) => metric?.value ?? 0;
const count = (value: number) => value.toLocaleString();

function customerInitial(name?: string) { return (name || "?").trim().charAt(0).toUpperCase() || "?"; }
function priorityTone(priority?: string) {
  if (priority === "urgent") return "bg-[var(--error-surface)] text-[var(--error-foreground)]";
  if (priority === "high") return "bg-[var(--warning-surface)] text-[var(--warning)]";
  return "bg-surface-wash text-muted-foreground";
}

export default function SupervisorDashboard() {
  const router = useRouter();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [platforms, setPlatforms] = useState<PlatformAnalytics | null>(null);
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null);
  const [attentionCustomers, setAttentionCustomers] = useState<CustomerAttentionResponse | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchData = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const [summaryRes, platformsRes, customerSummaryRes, attentionRes, teamRes, conversationsRes] = await Promise.all([
        fetchWithAuth("/api/v1/analytics/summary", { cache: "no-store" }),
        fetchWithAuth("/api/v1/analytics/platforms", { cache: "no-store" }),
        fetchWithAuth("/api/v1/analytics/customers/summary", { cache: "no-store" }),
        fetchWithAuth("/api/v1/analytics/customers/attention?limit=5&offset=0&sort_by=attention_score&sort_order=desc", { cache: "no-store" }),
        fetchWithAuth("/api/v1/team/members", { cache: "no-store" }),
        fetchWithAuth("/api/v1/inbox/conversations", { cache: "no-store" }),
      ]);
      const responses = [summaryRes, platformsRes, customerSummaryRes, attentionRes, teamRes, conversationsRes];
      if (responses.some((response) => response.status === 401 || response.status === 403)) {
        router.replace("/inbox");
        return;
      }
      if (responses.some((response) => !response.ok)) throw new Error("Dashboard request failed");
      const [nextSummary, nextPlatforms, nextCustomerSummary, nextAttention, nextTeam, nextConversations] = await Promise.all([
        summaryRes.json() as Promise<AnalyticsSummary>,
        platformsRes.json() as Promise<PlatformAnalytics>,
        customerSummaryRes.json() as Promise<CustomerSummary>,
        attentionRes.json() as Promise<CustomerAttentionResponse>,
        teamRes.json() as Promise<TeamMember[]>,
        conversationsRes.json() as Promise<Conversation[]>,
      ]);
      setSummary(nextSummary);
      setPlatforms(nextPlatforms);
      setCustomerSummary(nextCustomerSummary);
      setAttentionCustomers(nextAttention);
      setTeamMembers(Array.isArray(nextTeam) ? nextTeam : []);
      setConversations(Array.isArray(nextConversations) ? nextConversations : []);
    } catch {
      setError("Could not load the team command center. Please retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [router]);

  useEffect(() => {
    const role = localStorage.getItem("userRole") || "";
    if (!["supervisor", "business_admin"].includes(role)) {
      router.replace("/inbox");
      return;
    }
    void fetchData();
  }, [fetchData, router]);

  const priorityQueue = useMemo(() => conversations.filter((item) => ["urgent", "high"].includes(item.priority || "") || Boolean(item.unread)).sort((a, b) => {
    const order = { urgent: 0, high: 1 };
    return (order[a.priority as keyof typeof order] ?? 2) - (order[b.priority as keyof typeof order] ?? 2);
  }).slice(0, 8), [conversations]);

  if (loading) return <Loading />;
  const openWork = metricValue(summary?.metrics.open_conversations) + metricValue(summary?.metrics.pending_conversations);
  const waiting = metricValue(customerSummary?.metrics.customers_waiting_for_reply);
  const unassigned = platforms?.platforms.reduce((total, platform) => total + metricValue(platform.unassigned_conversations), 0) ?? 0;
  const urgentWork = conversations.filter((item) => ["urgent", "high"].includes(item.priority || "")).length;
  const cards = [
    { label: "Open workload", value: openWork, detail: "Open and pending conversations", icon: Inbox, tone: "text-accent-glow bg-accent/10" },
    { label: "Customers waiting", value: waiting, detail: "Latest message needs a reply", icon: Clock3, tone: "text-[var(--warning)] bg-[var(--warning-surface)]" },
    { label: "Priority queue", value: urgentWork, detail: "High or urgent conversations", icon: AlertTriangle, tone: "text-[var(--error-foreground)] bg-[var(--error-surface)]" },
    { label: "Unassigned", value: unassigned, detail: "Route these before queue builds", icon: UsersRound, tone: "text-blue-600 bg-blue-500/10" },
  ];

  return <main className="min-h-screen bg-background px-5 pb-12 pt-[92px] sm:px-8"><div className="mx-auto max-w-[1280px]">
    <header className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-2 text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">Supervisor workspace</p><h1 className="font-heading text-3xl font-black tracking-tight sm:text-4xl">Team command center</h1><p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">Route urgent work, protect response times, and keep your team focused on the customers who need help first.</p></div><div className="flex items-center gap-2"><Link href="/analytics" className="ds-button ds-button-secondary">View analytics</Link><button type="button" onClick={() => void fetchData(true)} disabled={refreshing} className="ds-button ds-button-secondary"><RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />Refresh</button></div></header>
    {error && <div role="alert" className="mb-6 rounded-2xl border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-sm text-[var(--error-foreground)]">{error}</div>}
    <div className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map((card, index) => <motion.section key={card.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-2xl border border-surface-border bg-surface p-5 shadow-sm"><div className={`mb-5 flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}><card.icon size={18} /></div><p className="text-[10px] font-black uppercase tracking-[0.17em] text-muted-foreground">{card.label}</p><p className="mt-1 font-heading text-3xl font-black tracking-tight">{count(card.value)}</p><p className="mt-2 text-xs text-muted-foreground">{card.detail}</p></motion.section>)}</div>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Act now</p><h2 className="mt-1 text-xl font-black tracking-tight">Priority queue</h2></div><Link href="/inbox" className="inline-flex items-center gap-1 text-xs font-bold text-accent-glow hover:underline">Open inbox <ArrowRight size={13} /></Link></div>{!priorityQueue.length ? <Empty label="Nothing urgent or unread right now" /> : <div className="space-y-2">{priorityQueue.map((conversation) => <Link key={conversation.id} href="/inbox" className="flex items-center gap-3 rounded-2xl border border-surface-border p-3.5 transition hover:border-accent/30 hover:bg-surface-wash"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{customerInitial(conversation.customer_name)}</div><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{conversation.customer_name || "Customer"}</p><p className="mt-1 truncate text-xs text-muted-foreground">{conversation.last_message || "No message preview"}</p></div><div className="flex shrink-0 flex-col items-end gap-1"><span className={`rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${priorityTone(conversation.priority)}`}>{conversation.priority || (conversation.unread ? "unread" : "open")}</span>{conversation.platform && <span className="text-[10px] text-muted-foreground">{conversation.platform}</span>}</div></Link>)}</div>}</section>
      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Customer risk</p><h2 className="mt-1 text-xl font-black tracking-tight">Needs follow-up</h2></div><ShieldAlert size={19} className="text-[var(--warning)]" /></div>{!attentionCustomers?.customers.length ? <Empty label="No customers need attention right now" /> : <div className="space-y-2">{attentionCustomers.customers.map((customer) => <Link key={customer.customer_id} href="/inbox" className="flex gap-3 rounded-2xl border border-surface-border p-3.5 transition hover:border-accent/30 hover:bg-surface-wash"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{customerInitial(customer.display_name)}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-bold">{customer.display_name}</p><p className="text-[11px] font-black text-[var(--warning)]">{Math.round(customer.attention_score)}</p></div><p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{customer.primary_reasons[0] || "Needs a support review"}</p></div></Link>)}</div>}</section>
    </div>
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Coverage check</p><h2 className="mt-1 text-xl font-black tracking-tight">Channel workload</h2></div><Link href="/analytics?view=channels" className="text-xs font-bold text-accent-glow hover:underline">Channel analytics</Link></div>{!platforms?.platforms.length ? <Empty label="No channel workload to show" /> : <div className="divide-y divide-surface-border">{[...platforms.platforms].sort((a, b) => metricValue(b.conversations) - metricValue(a.conversations)).slice(0, 4).map((platform) => <div key={platform.platform} className="flex items-center justify-between gap-4 py-4 first:pt-0"><div><p className="text-sm font-bold">{platform.display_name}</p><p className="mt-1 text-xs text-muted-foreground">{count(metricValue(platform.conversations))} conversations · {count(metricValue(platform.unanswered_conversations))} waiting</p></div><div className="text-right"><p className="text-sm font-black">{count(metricValue(platform.open_conversations) + metricValue(platform.pending_conversations))}</p><p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Open work</p></div></div>)}</div>}</section>
      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Team capacity</p><h2 className="mt-1 text-xl font-black tracking-tight">Who is available</h2></div><Link href="/team" className="text-xs font-bold text-accent-glow hover:underline">Manage team</Link></div>{!teamMembers.length ? <Empty label="No team members are available to display" /> : <div className="space-y-2">{teamMembers.slice(0, 6).map((member) => <div key={member.id} className="flex items-center gap-3 rounded-2xl border border-surface-border p-3"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{customerInitial(member.name || member.email)}</div><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{member.name || member.email || "Team member"}</p><p className="truncate text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{(member.role || "support").replace("_", " ")}</p></div><span className={member.status === "online" ? "text-xs font-bold text-[var(--success-foreground)]" : "text-xs text-muted-foreground"}>{member.status || "unknown"}</span></div>)}</div>}</section>
    </div>
  </div></main>;
}

function Loading() { return <div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>; }
function Empty({ label }: { label: string }) { return <div className="flex min-h-36 items-center justify-center rounded-2xl border border-dashed border-surface-border bg-surface-wash px-4 text-center text-sm text-muted-foreground">{label}</div>; }