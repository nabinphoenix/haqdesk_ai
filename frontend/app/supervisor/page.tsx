"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Brain, CheckCircle2, MessageCircle, RefreshCw, Users } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type TeamMember = { id: number; name: string; role: string; status: string };
type Conversation = { id: number; customer_name: string; last_message: string; priority: string };
type Analytics = { open_conversations?: number; ai_drafts_generated?: number };

export default function SupervisorDashboard() {
  const router = useRouter();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [urgentConversations, setUrgentConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [analyticsRes, teamRes, conversationsRes] = await Promise.all([
        fetchWithAuth("/api/v1/analytics/summary"),
        fetchWithAuth("/api/v1/team/members"),
        fetchWithAuth("/api/v1/inbox/conversations"),
      ]);
      if ([analyticsRes, teamRes, conversationsRes].some((res) => res.status === 401 || res.status === 403)) {
        router.replace("/inbox");
        return;
      }
      if (!analyticsRes.ok || !teamRes.ok || !conversationsRes.ok) throw new Error("Dashboard request failed");
      const conversations: Conversation[] = await conversationsRes.json();
      setAnalytics(await analyticsRes.json());
      setTeamMembers(await teamRes.json());
      setUrgentConversations(conversations.filter((item) => ["urgent", "high"].includes(item.priority)));
    } catch {
      setError("Could not load the team overview. Please retry.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!['supervisor', 'business_admin'].includes(localStorage.getItem('userRole') || '')) {
      router.replace('/inbox');
      return;
    }
    void fetchData();
  }, [fetchData, router]);

  if (loading) return <Loading />;

  const cards = [
    { label: "Open Conversations", value: analytics?.open_conversations ?? 0, icon: MessageCircle, color: "text-accent-glow", bg: "bg-accent/10" },
    { label: "Team Members", value: teamMembers.length, icon: Users, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Urgent / High", value: urgentConversations.length, icon: AlertTriangle, color: "text-[var(--error-foreground)]", bg: "bg-[var(--error-surface)]" },
    { label: "AI Drafts", value: analytics?.ai_drafts_generated ?? 0, icon: Brain, color: "text-accent-glow", bg: "bg-accent/10" },
  ];

  return <main className="min-h-screen bg-background px-6 pb-12 pt-[92px]">
    <div className="mx-auto max-w-[1120px]">
      <header className="mb-8 flex items-start justify-between">
        <div><p className="mb-1 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-accent-glow"><Activity size={15} />Supervisor</p>
          <h1 className="text-2xl font-black">Team Overview</h1><p className="mt-1 text-sm text-muted-foreground">Monitor your team and escalated conversations</p></div>
        <button onClick={() => void fetchData()} className="flex items-center gap-2 rounded-xl border border-border px-4 py-2 text-sm text-muted-foreground hover:bg-muted"><RefreshCw size={14} />Refresh</button>
      </header>
      {error && <div className="mb-6 rounded-xl border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-sm text-[var(--error-foreground)]">{error}</div>}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">{cards.map((card, index) => <motion.section key={card.label} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * .06 }} className="ds-card p-5">
        <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl ${card.bg}`}><card.icon size={16} className={card.color} /></div><p className="text-2xl font-black">{card.value}</p><p className="mt-1 text-xs text-muted-foreground">{card.label}</p>
      </motion.section>)}</div>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="ds-card p-6"><h2 className="mb-4 flex items-center gap-2 text-sm font-bold"><AlertTriangle size={14} className="text-[var(--error-foreground)]" />Urgent & High Priority</h2>
          {!urgentConversations.length ? <Empty icon={CheckCircle2} label="No urgent conversations" /> : <div className="space-y-3">{urgentConversations.slice(0, 6).map((conversation) => <button key={conversation.id} onClick={() => router.push('/inbox')} className="flex w-full items-center gap-3 rounded-xl border border-border p-3 text-left hover:bg-muted"><span className={`h-2 w-2 rounded-full ${conversation.priority === 'urgent' ? 'bg-[var(--error)]' : 'bg-orange-400'}`} /><span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold">{conversation.customer_name}</span><span className="block truncate text-xs text-muted-foreground">{conversation.last_message}</span></span><span className="text-[10px] font-bold uppercase text-[var(--error-foreground)]">{conversation.priority}</span></button>)}</div>}
        </section>
        <section className="ds-card p-6"><h2 className="mb-4 flex items-center gap-2 text-sm font-bold"><Users size={14} className="text-blue-400" />Team Status</h2><div className="space-y-3">{teamMembers.map((member) => <div key={member.id} className="flex items-center gap-3 rounded-xl border border-border p-3"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-xs font-bold text-accent-glow">{member.name?.charAt(0) || '?'}</div><div className="flex-1"><p className="text-sm font-semibold">{member.name}</p><p className="text-[10px] uppercase text-muted-foreground">{member.role?.replace('_', ' ')}</p></div><span className={member.status === 'online' ? 'text-xs text-[var(--success-foreground)]' : 'text-xs text-muted-foreground'}>{member.status}</span></div>)}</div></section>
      </div>
    </div>
  </main>;
}

function Loading() { return <div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>; }
function Empty({ icon: Icon, label }: { icon: typeof CheckCircle2; label: string }) { return <div className="flex flex-col items-center gap-2 py-10 text-muted-foreground"><Icon size={28} className="text-[var(--success-foreground)]" /><p className="text-xs">{label}</p></div>; }
