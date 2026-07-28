"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MessageCircle, Bot, Clock, Target, TrendingUp, Zap, BarChart3, Activity, Users } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

export default function AnalyticsDashboard() {
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetchWithAuth("/api/v1/analytics/summary");
        if (res.ok) {
          const data = await res.json();
          setAnalyticsData(data);
        }
      } catch (e) {
        console.error("Failed to fetch analytics", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  const kpis = analyticsData ? [
    { label: "Total Messages", value: analyticsData.total_messages.toLocaleString(), delta: "All time", icon: MessageCircle, color: "#818CF8" },
    { label: "AI Drafts Generated", value: analyticsData.ai_drafts_generated.toLocaleString(), delta: "All time", icon: Bot, color: "#06B6D4" },
    { label: "Total Conversations", value: analyticsData.total_conversations.toLocaleString(), delta: `${analyticsData.open_conversations} open`, icon: Activity, color: "#10B981" },
    { label: "Total Customers", value: analyticsData.total_customers.toLocaleString(), delta: "Across all platforms", icon: Users, color: "#F59E0B" },
  ] : [];

  const platformStats = analyticsData ? Object.entries(analyticsData.platform_breakdown).map(([platform, count]: any) => {
    const total = analyticsData.total_conversations || 1;
    return {
      name: platform.charAt(0).toUpperCase() + platform.slice(1),
      messages: count,
      pct: Math.round((count / total) * 100),
      color: platform === "facebook" ? "bg-blue-500" : platform === "instagram" ? "bg-pink-500" : platform === "email" ? "bg-yellow-500" : "bg-green-500"
    };
  }) : [];

  const barData = analyticsData?.messages_per_day?.map((d: any) => d.count) || [];

  const recentActivity = analyticsData ? [
    { label: "AI Drafts Generated", value: analyticsData.ai_drafts_generated.toLocaleString(), delta: "All time" },
    { label: "Knowledge Docs", value: analyticsData.knowledge_documents.toLocaleString(), delta: `${analyticsData.knowledge_chunks} chunks` },
    { label: "Team Members", value: analyticsData.team_members.toLocaleString(), delta: "Active" },
    { label: "Open Conversations", value: analyticsData.open_conversations.toLocaleString(), delta: "Requiring attention" },
  ] : [];
  return (
    <div className="page-padded font-body">
      <div className="page-shell">
        <header className="page-header">
          <div className="page-header-row">
            <div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-surface-border rounded-lg text-[#818CF8] text-[9px] font-black uppercase tracking-widest mb-4"
              >
                <Zap size={12} strokeWidth={3} />
                Live Data
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-4xl sm:text-5xl text-foreground">Analytics</h1>
              <p className="text-sm font-medium mt-2" style={{ color: "var(--muted-foreground)" }}>
                Track your team performance and AI support activity in real time.
              </p>
            </div>
            <div className="flex gap-3 mt-4 sm:mt-0">
              <button className="px-6 py-3 bg-white/5 border border-surface-border rounded-xl text-[10px] font-black uppercase tracking-widest text-foreground hover:bg-white/10 transition-all">
                Export Report
              </button>
              <button className="px-6 py-3 bg-[#6D4AE2] text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover-glow transition-all active:scale-95 shadow-xl shadow-purple-950/20">
                Refresh
              </button>
            </div>
          </div>
        </header>

        <div className="page-body custom-scrollbar space-y-8">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* KPI cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
                {kpis.map((kpi, i) => (
                  <motion.div
                    key={kpi.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="p-6 rounded-[2rem] bg-white/5 border border-surface-border hover:border-[#818CF8]/20 transition-all group"
                  >
                    <div className="flex justify-between items-start mb-5">
                      <div className="p-2.5 bg-white/5 border border-surface-border rounded-xl group-hover:bg-[#6D4AE2] group-hover:text-white transition-all" style={{ color: kpi.color }}>
                        <kpi.icon size={18} strokeWidth={2.5} />
                      </div>
                      <div className="flex items-center gap-1 px-2 py-0.5 bg-emerald-950/30 border border-emerald-900/40 text-emerald-400 rounded-lg text-[9px] font-black uppercase">
                        <TrendingUp size={9} strokeWidth={3} />
                        {kpi.delta}
                      </div>
                    </div>
                    <p className="text-[9px] font-black uppercase tracking-[0.3em] mb-1.5" style={{ color: "var(--muted-foreground)" }}>{kpi.label}</p>
                    <div className="text-3xl font-heading font-black tracking-tighter text-foreground">{kpi.value}</div>
                  </motion.div>
                ))}
              </div>

              {/* Chart + Platform breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Bar chart */}
                <div className="lg:col-span-2 p-8 rounded-[2.5rem] bg-white/5 border border-surface-border">
                  <div className="flex items-center gap-3 mb-6">
                    <BarChart3 size={16} className="text-[#818CF8]" />
                    <div>
                      <h3 className="text-sm font-black uppercase tracking-widest text-foreground">Message Volume</h3>
                      <p className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>Daily volume last 7 days</p>
                    </div>
                  </div>
                  <div className="h-[200px] flex items-end gap-1.5 justify-center">
                    {barData.length === 0 ? (
                      <p className="text-xs text-slate-500 self-center">No messages sent in the last 7 days</p>
                    ) : (
                      barData.map((h: number, i: number) => {
                        const maxVal = Math.max(...barData, 1);
                        const pctHeight = Math.round((h / maxVal) * 100);
                        return (
                          <div
                            key={i}
                            className="flex-1 max-w-[40px] rounded-t-lg bg-gradient-to-t from-[#6D4AE2]/40 to-[#818CF8] transition-all hover:opacity-80"
                            style={{ height: `${pctHeight}%` }}
                            title={`${h} messages on ${analyticsData?.messages_per_day?.[i]?.date}`}
                          />
                        );
                      })
                    )}
                  </div>
                  <div className="flex justify-between mt-3 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                    {analyticsData?.messages_per_day?.length > 0 ? (
                      <>
                        <span>{analyticsData.messages_per_day[0].date}</span>
                        <span>{analyticsData.messages_per_day[analyticsData.messages_per_day.length - 1].date}</span>
                      </>
                    ) : (
                      <span>No dates available</span>
                    )}
                  </div>
                </div>

                {/* Platform breakdown */}
                <div className="p-8 rounded-[2.5rem] bg-white/5 border border-surface-border">
                  <div className="flex items-center gap-3 mb-6">
                    <Activity size={16} className="text-[#818CF8]" />
                    <div>
                      <h3 className="text-sm font-black uppercase tracking-widest text-foreground">By Platform</h3>
                      <p className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>Message distribution</p>
                    </div>
                  </div>
                  <div className="space-y-5">
                    {platformStats.map((p: any) => (
                      <div key={p.name}>
                        <div className="flex justify-between mb-1.5">
                          <span className="text-[11px] font-bold text-foreground">{p.name}</span>
                          <span className="text-[11px] font-black text-slate-400">{p.messages.toLocaleString()}</span>
                        </div>
                        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                          <div className={`h-full rounded-full ${p.color}`} style={{ width: `${p.pct}%` }} />
                        </div>
                      </div>
                    ))}
                    {platformStats.length === 0 && (
                      <p className="text-xs text-slate-500">No platform breakdown data available</p>
                    )}
                  </div>
                </div>
              </div>

              {/* AI stats row */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
                {recentActivity.map((a, i) => (
                  <motion.div
                    key={a.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-5 rounded-[2rem] bg-white/5 border border-surface-border"
                  >
                    <p className="text-[9px] font-black uppercase tracking-widest mb-2" style={{ color: "var(--muted-foreground)" }}>{a.label}</p>
                    <p className="text-2xl font-black tracking-tighter text-foreground">{a.value}</p>
                    <p className="text-[10px] font-bold text-emerald-400 mt-1">{a.delta}</p>
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}