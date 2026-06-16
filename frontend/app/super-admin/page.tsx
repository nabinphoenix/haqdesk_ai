"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Building2,
  Users,
  Brain,
  Activity,
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Trash2,
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  Globe,
  Database,
  Cpu,
  DollarSign,
} from "lucide-react";

// --- Mock Data ---
const mockBusinesses = [
  { id: 1, name: "TechSuru Pvt Ltd", owner: "Nabin Nepali", plan: "Pro", status: "active", messages: 1240, agents: 4, joined: "2025-01-15", revenue: "$49" },
  { id: 2, name: "Sasto Pasal", owner: "Ramesh KC", plan: "Starter", status: "active", messages: 430, agents: 2, joined: "2025-02-20", revenue: "$19" },
  { id: 3, name: "Kathmandu Eats", owner: "Sita Sharma", plan: "Pro", status: "suspended", messages: 890, agents: 3, joined: "2025-03-10", revenue: "$49" },
  { id: 4, name: "Nepal Treks", owner: "Hari Thapa", plan: "Enterprise", status: "active", messages: 3200, agents: 10, joined: "2025-01-05", revenue: "$149" },
  { id: 5, name: "Digital Pasal", owner: "Rita Gurung", plan: "Starter", status: "inactive", messages: 120, agents: 1, joined: "2025-04-01", revenue: "$19" },
];

const mockStats = [
  { label: "Total Businesses", value: "24", change: "+3 this month", icon: Building2, color: "text-purple-400", bg: "bg-purple-500/10" },
  { label: "Total Users", value: "142", change: "+12 this month", icon: Users, color: "text-blue-400", bg: "bg-blue-500/10" },
  { label: "AI Drafts Generated", value: "18,420", change: "+2.1k this week", icon: Brain, color: "text-green-400", bg: "bg-green-500/10" },
  { label: "Monthly Revenue", value: "$1,840", change: "+18% vs last month", icon: DollarSign, color: "text-yellow-400", bg: "bg-yellow-500/10" },
  { label: "Active Integrations", value: "67", change: "FB + IG + WA", icon: Globe, color: "text-cyan-400", bg: "bg-cyan-500/10" },
  { label: "System Uptime", value: "99.9%", change: "Last 30 days", icon: Activity, color: "text-emerald-400", bg: "bg-emerald-500/10" },
];

const mockSystemHealth = [
  { label: "FastAPI Backend", status: "healthy", latency: "12ms" },
  { label: "PostgreSQL + pgvector", status: "healthy", latency: "4ms" },
  { label: "RAG Pipeline", status: "healthy", latency: "1.8s" },
  { label: "Groq LLM API", status: "healthy", latency: "1.2s" },
  { label: "Redis Queue", status: "warning", latency: "45ms" },
  { label: "Meta Webhook", status: "healthy", latency: "220ms" },
];

const mockRecentActivity = [
  { id: 1, action: "New business registered", target: "Digital Pasal", time: "2m ago", type: "success" },
  { id: 2, action: "RAG document uploaded", target: "TechSuru Pvt Ltd", time: "15m ago", type: "info" },
  { id: 3, action: "Business suspended", target: "Kathmandu Eats", time: "1h ago", type: "warning" },
  { id: 4, action: "New agent added", target: "Nepal Treks", time: "2h ago", type: "success" },
  { id: 5, action: "Webhook failure", target: "Sasto Pasal", time: "3h ago", type: "error" },
];

type Tab = "overview" | "businesses" | "system" | "activity";

export default function SuperAdminDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const role = localStorage.getItem("userRole");
    if (role !== "super_admin") {
      router.push("/inbox");
    }
  }, [router]);

  if (!mounted) return null;

  const filteredBusinesses = mockBusinesses.filter((b) => {
    const matchesSearch = b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.owner.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || b.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "businesses", label: "Businesses", icon: Building2 },
    { id: "system", label: "System Health", icon: Cpu },
    { id: "activity", label: "Activity Log", icon: Shield },
  ];

  return (
    <div className="min-h-screen bg-[#090514] pt-[60px]">
      <div className="max-w-[1280px] mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield size={18} className="text-purple-400" />
              <span className="text-xs font-bold uppercase tracking-widest text-purple-400">
                Super Admin
              </span>
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">
              HaqDesk AI Control Center
            </h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Manage all businesses, users, and system health
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-gray-400 hover:bg-white/5 hover:text-white transition-all text-sm">
              <RefreshCw size={14} />
              Refresh
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white transition-all text-sm font-medium">
              <Plus size={14} />
              Add Business
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-8 border-b border-white/10">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all border-b-2 -mb-px ${
                  activeTab === tab.id
                    ? "border-purple-500 text-white"
                    : "border-transparent text-gray-400 hover:text-white"
                }`}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>

            {/* Stats grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {mockStats.map((stat, i) => {
                const Icon = stat.icon;
                return (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:bg-white/[0.06] transition-all"
                  >
                    <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center mb-3`}>
                      <Icon size={18} className={stat.color} />
                    </div>
                    <p className="text-2xl font-black text-white mb-0.5">{stat.value}</p>
                    <p className="text-xs font-medium text-gray-400">{stat.label}</p>
                    <p className="text-[11px] text-green-400 mt-1">{stat.change}</p>
                  </motion.div>
                );
              })}
            </div>

            {/* Bottom row: top businesses + recent activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Top businesses by messages */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <TrendingUp size={14} className="text-purple-400" />
                  Top Businesses by Activity
                </h3>
                <div className="space-y-3">
                  {mockBusinesses
                    .sort((a, b) => b.messages - a.messages)
                    .slice(0, 4)
                    .map((b) => (
                      <div key={b.id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-xs font-bold">
                            {b.name.charAt(0)}
                          </div>
                          <div>
                            <p className="text-[13px] font-semibold text-white">{b.name}</p>
                            <p className="text-[11px] text-gray-400">{b.plan} plan</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[13px] font-bold text-white">{b.messages.toLocaleString()}</p>
                          <p className="text-[11px] text-gray-400">messages</p>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Recent activity */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Activity size={14} className="text-cyan-400" />
                  Recent Activity
                </h3>
                <div className="space-y-3">
                  {mockRecentActivity.map((a) => (
                    <div key={a.id} className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                        a.type === "success" ? "bg-green-400" :
                        a.type === "warning" ? "bg-yellow-400" :
                        a.type === "error" ? "bg-red-400" :
                        "bg-blue-400"
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] text-white">{a.action}</p>
                        <p className="text-[11px] text-gray-400">{a.target} · {a.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </motion.div>
        )}

        {/* BUSINESSES TAB */}
        {activeTab === "businesses" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>

            {/* Filters */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search businesses or owners..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-[13px] text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-[13px] text-white focus:border-purple-500 focus:outline-none transition-all"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
                <option value="inactive">Inactive</option>
              </select>
              <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 text-gray-400 hover:bg-white/5 hover:text-white transition-all text-[13px]">
                <Download size={14} />
                Export
              </button>
            </div>

            {/* Table */}
            <div className="rounded-2xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.03]">
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Business</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Owner</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Plan</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Status</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Messages</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Agents</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Revenue</th>
                    <th className="text-left px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBusinesses.map((b, i) => (
                    <tr
                      key={b.id}
                      className="border-b border-white/5 hover:bg-white/[0.03] transition-all"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-xs font-bold shrink-0">
                            {b.name.charAt(0)}
                          </div>
                          <span className="text-[13px] font-semibold text-white">{b.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[13px] text-gray-300">{b.owner}</td>
                      <td className="px-4 py-3">
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                          b.plan === "Enterprise" ? "bg-yellow-500/20 text-yellow-400" :
                          b.plan === "Pro" ? "bg-purple-500/20 text-purple-400" :
                          "bg-gray-500/20 text-gray-400"
                        }`}>
                          {b.plan}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1.5 text-[11px] font-bold w-fit px-2 py-0.5 rounded-full ${
                          b.status === "active" ? "bg-green-500/20 text-green-400" :
                          b.status === "suspended" ? "bg-red-500/20 text-red-400" :
                          "bg-gray-500/20 text-gray-400"
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            b.status === "active" ? "bg-green-400" :
                            b.status === "suspended" ? "bg-red-400" :
                            "bg-gray-400"
                          }`} />
                          {b.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[13px] text-gray-300">{b.messages.toLocaleString()}</td>
                      <td className="px-4 py-3 text-[13px] text-gray-300">{b.agents}</td>
                      <td className="px-4 py-3 text-[13px] font-semibold text-green-400">{b.revenue}/mo</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button className="p-1.5 rounded-lg text-gray-400 hover:bg-white/10 hover:text-white transition-all">
                            <Eye size={13} />
                          </button>
                          <button className="p-1.5 rounded-lg text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-all">
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-xs text-gray-500 mt-3">{filteredBusinesses.length} businesses found</p>
          </motion.div>
        )}

        {/* SYSTEM HEALTH TAB */}
        {activeTab === "system" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Service status */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                <h3 className="text-sm font-bold text-white mb-5 flex items-center gap-2">
                  <Cpu size={14} className="text-purple-400" />
                  Service Status
                </h3>
                <div className="space-y-3">
                  {mockSystemHealth.map((s) => (
                    <div key={s.label} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5">
                      <div className="flex items-center gap-3">
                        {s.status === "healthy" ? (
                          <CheckCircle size={15} className="text-green-400" />
                        ) : s.status === "warning" ? (
                          <AlertTriangle size={15} className="text-yellow-400" />
                        ) : (
                          <XCircle size={15} className="text-red-400" />
                        )}
                        <span className="text-[13px] font-medium text-white">{s.label}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-gray-400">{s.latency}</span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                          s.status === "healthy" ? "bg-green-500/20 text-green-400" :
                          s.status === "warning" ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-red-500/20 text-red-400"
                        }`}>
                          {s.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Database stats */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                <h3 className="text-sm font-bold text-white mb-5 flex items-center gap-2">
                  <Database size={14} className="text-cyan-400" />
                  Database Stats
                </h3>
                <div className="space-y-4">
                  {[
                    { label: "Total Messages", value: "48,210", bar: 82 },
                    { label: "Knowledge Chunks", value: "12,440", bar: 45 },
                    { label: "Vector Embeddings", value: "12,440", bar: 45 },
                    { label: "Active Conversations", value: "1,820", bar: 31 },
                    { label: "DB Storage Used", value: "2.4 GB", bar: 24 },
                  ].map((d) => (
                    <div key={d.label}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[12px] text-gray-400">{d.label}</span>
                        <span className="text-[13px] font-bold text-white">{d.value}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-cyan-500"
                          style={{ width: `${d.bar}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </motion.div>
        )}

        {/* ACTIVITY LOG TAB */}
        {activeTab === "activity" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="rounded-2xl border border-white/10 overflow-hidden">
              <div className="border-b border-white/10 bg-white/[0.03] px-5 py-3 flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">System Activity Log</h3>
                <button className="flex items-center gap-2 text-[12px] text-gray-400 hover:text-white transition-all">
                  <Download size={13} />
                  Export Log
                </button>
              </div>
              <div className="divide-y divide-white/5">
                {[...mockRecentActivity, ...mockRecentActivity].map((a, i) => (
                  <div key={i} className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/[0.02] transition-all">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${
                      a.type === "success" ? "bg-green-400" :
                      a.type === "warning" ? "bg-yellow-400" :
                      a.type === "error" ? "bg-red-400" :
                      "bg-blue-400"
                    }`} />
                    <div className="flex-1">
                      <p className="text-[13px] text-white">{a.action}</p>
                      <p className="text-[11px] text-gray-400">{a.target}</p>
                    </div>
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                      a.type === "success" ? "bg-green-500/20 text-green-400" :
                      a.type === "warning" ? "bg-yellow-500/20 text-yellow-400" :
                      a.type === "error" ? "bg-red-500/20 text-red-400" :
                      "bg-blue-500/20 text-blue-400"
                    }`}>
                      {a.type}
                    </span>
                    <span className="text-[11px] text-gray-500 w-16 text-right">{a.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

      </div>
    </div>
  );
}
