"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, Clock, Inbox, MessageCircle, RefreshCw, TrendingUp } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type Conversation = { id: number; customer_name: string; last_message: string; status: string; unread: number };

export default function AgentDashboard() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [agentName, setAgentName] = useState("Agent");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const response = await fetchWithAuth("/api/v1/inbox/conversations");
      if (response.status === 401 || response.status === 403) { router.replace('/login'); return; }
      if (!response.ok) throw new Error("Queue request failed");
      setConversations(await response.json());
    } catch { setError("Could not load your support queue. Please retry."); }
    finally { setLoading(false); }
  }, [router]);

  useEffect(() => {
    const role = localStorage.getItem('userRole') || '';
    setAgentName(localStorage.getItem('userName') || 'Agent');
    if (!['agent', 'business_admin', 'supervisor'].includes(role)) { router.replace('/inbox'); return; }
    void fetchData();
  }, [fetchData, router]);

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>;
  const open = conversations.filter((item) => item.status === 'open');
  const resolved = conversations.filter((item) => item.status === 'resolved');
  const unread = conversations.filter((item) => item.unread > 0);
  const cards = [
    { label: 'Open Conversations', value: open.length, icon: MessageCircle, color: 'text-accent-glow' },
    { label: 'Needs Response', value: unread.length, icon: Clock, color: 'text-[var(--warning)]' },
    { label: 'Resolved', value: resolved.length, icon: CheckCircle2, color: 'text-[var(--success-foreground)]' },
  ];

  return <main className="min-h-screen bg-background px-6 pb-12 pt-[92px]"><div className="mx-auto max-w-[900px]">
    <header className="mb-8 flex items-center justify-between"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent font-bold text-on-accent">{agentName.charAt(0).toUpperCase()}</div><div><h1 className="text-xl font-black">Welcome back, {agentName}!</h1><p className="text-sm text-muted-foreground">Here&apos;s your support queue for today</p></div></div><button onClick={() => void fetchData()} aria-label="Refresh queue" className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-muted"><RefreshCw size={15} /></button></header>
    {error && <div className="mb-6 rounded-xl border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-sm text-[var(--error-foreground)]">{error}</div>}
    <div className="mb-8 grid grid-cols-3 gap-4">{cards.map((card, index) => <motion.section key={card.label} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * .07 }} className="ds-card p-5 text-center"><card.icon size={18} className={`mx-auto mb-3 ${card.color}`} /><p className="text-2xl font-black">{card.value}</p><p className="mt-1 text-xs text-muted-foreground">{card.label}</p></motion.section>)}</div>
    <button onClick={() => router.push('/inbox')} className="mb-8 flex w-full items-center gap-4 rounded-2xl border border-accent/30 bg-accent/10 p-5 text-left hover:bg-accent/15"><div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-on-accent"><Inbox size={20} /></div><div><p className="font-bold">Go to Inbox</p><p className="text-xs text-muted-foreground">{unread.length ? `${unread.length} conversation${unread.length === 1 ? '' : 's'} need your response` : 'All caught up — no pending responses'}</p></div>{unread.length > 0 && <span className="ml-auto rounded-full bg-[var(--error)] px-2 py-1 text-xs font-bold text-on-accent">{unread.length}</span>}</button>
    <section className="ds-card p-6"><h2 className="mb-4 flex items-center gap-2 text-sm font-bold"><TrendingUp size={14} className="text-accent-glow" />Recent Conversations</h2>{!conversations.length ? <div className="py-10 text-center text-xs text-muted-foreground">No conversations yet</div> : <div className="space-y-3">{conversations.slice(0, 8).map((conversation) => <button key={conversation.id} onClick={() => router.push('/inbox')} className="flex w-full items-center gap-3 rounded-xl border border-border p-3 text-left hover:bg-muted"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-xs font-bold text-accent-glow">{conversation.customer_name?.charAt(0) || '?'}</div><div className="min-w-0 flex-1"><p className={`truncate text-sm ${conversation.unread ? 'font-bold' : 'font-medium'}`}>{conversation.customer_name}</p><p className="truncate text-xs text-muted-foreground">{conversation.last_message}</p></div><span className="text-[10px] uppercase text-muted-foreground">{conversation.status}</span></button>)}</div>}</section>
  </div></main>;
}
