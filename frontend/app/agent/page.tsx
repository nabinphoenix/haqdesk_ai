"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Inbox, MessageCircleMore, RefreshCw } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type Conversation = {
  id: number;
  customer_name?: string;
  last_message?: string;
  status?: string;
  unread?: number;
  priority?: string;
  platform?: string;
  updated_at?: string;
};

function initial(name?: string) { return (name || "?").trim().charAt(0).toUpperCase() || "?"; }
function priorityTone(priority?: string, unread?: number) {
  if (priority === "urgent") return "bg-[var(--error-surface)] text-[var(--error-foreground)]";
  if (priority === "high" || unread) return "bg-[var(--warning-surface)] text-[var(--warning)]";
  return "bg-surface-wash text-muted-foreground";
}

export default function AgentDashboard() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [agentName, setAgentName] = useState("Agent");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchData = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const response = await fetchWithAuth("/api/v1/inbox/conversations", { cache: "no-store" });
      if (response.status === 401 || response.status === 403) { router.replace("/login"); return; }
      if (!response.ok) throw new Error("Queue request failed");
      const payload = await response.json() as Conversation[];
      setConversations(Array.isArray(payload) ? payload : []);
    } catch {
      setError("Could not load your support queue. Please retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [router]);

  useEffect(() => {
    const role = localStorage.getItem("userRole") || "";
    setAgentName(localStorage.getItem("userName") || "Agent");
    if (role === "business_admin") { router.replace("/analytics"); return; }
    if (role === "supervisor") { router.replace("/supervisor"); return; }
    if (role !== "agent") { router.replace("/inbox"); return; }
    void fetchData();
  }, [fetchData, router]);

  const open = conversations.filter((item) => ["open", "pending"].includes(item.status || ""));
  const needsResponse = conversations.filter((item) => Boolean(item.unread));
  const priority = conversations.filter((item) => ["urgent", "high"].includes(item.priority || ""));
  const resolved = conversations.filter((item) => item.status === "resolved");
  const nextUp = useMemo(() => [...conversations].filter((item) => Boolean(item.unread) || ["urgent", "high"].includes(item.priority || "") || ["open", "pending"].includes(item.status || "")).sort((a, b) => {
    const urgency = { urgent: 0, high: 1 };
    const aRank = urgency[a.priority as keyof typeof urgency] ?? (a.unread ? 2 : 3);
    const bRank = urgency[b.priority as keyof typeof urgency] ?? (b.unread ? 2 : 3);
    return aRank - bRank;
  }).slice(0, 8), [conversations]);

  if (loading) return <Loading />;
  const cards = [
    { label: "My open work", value: open.length, detail: "Open or pending conversations", icon: MessageCircleMore, tone: "text-accent-glow bg-accent/10" },
    { label: "Needs my reply", value: needsResponse.length, detail: "Unread customer messages", icon: Clock3, tone: "text-[var(--warning)] bg-[var(--warning-surface)]" },
    { label: "High priority", value: priority.length, detail: "High or urgent conversations", icon: AlertTriangle, tone: "text-[var(--error-foreground)] bg-[var(--error-surface)]" },
    { label: "Resolved", value: resolved.length, detail: "Resolved conversations in your queue", icon: CheckCircle2, tone: "text-[var(--success-foreground)] bg-[var(--success-surface)]" },
  ];

  return <main className="min-h-screen bg-background px-5 pb-12 pt-[92px] sm:px-8"><div className="mx-auto max-w-[1120px]">
    <header className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent font-heading text-lg font-black text-on-accent">{initial(agentName)}</div><div><p className="text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">My work</p><h1 className="mt-1 font-heading text-3xl font-black tracking-tight">Good to see you, {agentName}.</h1><p className="mt-1 text-sm text-muted-foreground">Start with the customers who are waiting for you.</p></div></div><button type="button" onClick={() => void fetchData(true)} disabled={refreshing} className="ds-button ds-button-secondary"><RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />Refresh queue</button></header>
    {error && <div role="alert" className="mb-6 rounded-2xl border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-sm text-[var(--error-foreground)]">{error}</div>}
    <section className="mb-7 rounded-[2rem] border border-accent/20 bg-gradient-to-br from-accent/10 via-surface to-blue-500/5 p-5 sm:p-6"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-[10px] font-black uppercase tracking-[0.19em] text-accent-glow">Your next action</p><h2 className="mt-2 text-xl font-black tracking-tight">{needsResponse.length ? `${needsResponse.length} customer${needsResponse.length === 1 ? " is" : "s are"} waiting for your reply.` : "Your queue is clear of unread customer messages."}</h2><p className="mt-2 text-sm text-muted-foreground">Open the inbox to reply, use AI suggestions, and resolve conversations when they are complete.</p></div><Link href="/inbox" className="ds-button ds-button-primary shrink-0">Open my inbox <ArrowRight size={15} /></Link></div></section>
    <div className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map((card, index) => <motion.section key={card.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-2xl border border-surface-border bg-surface p-5 shadow-sm"><div className={`mb-5 flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}><card.icon size={18} /></div><p className="text-[10px] font-black uppercase tracking-[0.17em] text-muted-foreground">{card.label}</p><p className="mt-1 font-heading text-3xl font-black tracking-tight">{card.value.toLocaleString()}</p><p className="mt-2 text-xs text-muted-foreground">{card.detail}</p></motion.section>)}</div>
    <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Work queue</p><h2 className="mt-1 text-xl font-black tracking-tight">What to handle next</h2></div><Link href="/inbox" className="inline-flex items-center gap-1 text-xs font-bold text-accent-glow hover:underline">Full inbox <ArrowRight size={13} /></Link></div>{!nextUp.length ? <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-surface-border bg-surface-wash px-4 text-center"><CheckCircle2 size={28} className="text-[var(--success-foreground)]" /><p className="text-sm font-bold">You&apos;re all caught up</p><p className="text-xs text-muted-foreground">New assigned conversations will appear here.</p></div> : <div className="grid gap-3 md:grid-cols-2">{nextUp.map((conversation) => <Link key={conversation.id} href="/inbox" className="flex items-center gap-3 rounded-2xl border border-surface-border p-4 transition hover:border-accent/30 hover:bg-surface-wash"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{initial(conversation.customer_name)}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className={`truncate text-sm ${conversation.unread ? "font-black" : "font-bold"}`}>{conversation.customer_name || "Customer"}</p><span className={`rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${priorityTone(conversation.priority, conversation.unread)}`}>{conversation.priority || (conversation.unread ? "new" : conversation.status || "open")}</span></div><p className="mt-1 truncate text-xs text-muted-foreground">{conversation.last_message || "No message preview"}</p><div className="mt-2 flex gap-2 text-[10px] font-bold text-muted-foreground"><span>{conversation.platform || "Support"}</span><span className="uppercase">{conversation.status || "open"}</span></div></div></Link>)}</div>}</section>
  </div></main>;
}

function Loading() { return <div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>; }