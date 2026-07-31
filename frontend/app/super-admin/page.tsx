"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity, Brain, Building2, Cpu, Database, Globe, MessageSquare,
  RefreshCw, Search, Shield, Users,
} from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type Tab = "overview" | "businesses" | "system" | "activity";
type Stat = { key: string; label: string; value: number; change: string };
type Business = {
  id: number; name: string; owner: string; status: string; users: number;
  agents: number; messages: number; joined: string | null;
};
type ActivityItem = {
  action: string; target: string; type: "success" | "info" | "warning" | "error";
  timestamp: string | null;
};
type Dashboard = {
  stats: Stat[];
  businesses: Business[];
  recent_activity: ActivityItem[];
  database_stats: { label: string; value: number }[];
  system_health: { label: string; status: string; detail: string }[];
  generated_at: string;
};

const statIcons: Record<string, typeof Building2> = {
  businesses: Building2, users: Users, ai_drafts: Brain, messages: MessageSquare,
  integrations: Globe, conversations: Activity,
};

function relativeTime(value: string | null) {
  if (!value) return "Unknown time";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default function SuperAdminDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetchWithAuth("/api/v1/super-admin/dashboard");
      if (response.status === 401 || response.status === 403) {
        router.replace("/inbox");
        return;
      }
      if (!response.ok) throw new Error("Dashboard request failed");
      setData(await response.json());
    } catch {
      setError("Could not load platform data. Please retry.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (localStorage.getItem("userRole") !== "super_admin") {
      router.replace("/inbox");
      return;
    }
    void loadDashboard();
  }, [loadDashboard, router]);

  const filteredBusinesses = useMemo(() => (data?.businesses ?? []).filter((business) => {
    const query = searchQuery.toLowerCase();
    return (business.name.toLowerCase().includes(query) || business.owner.toLowerCase().includes(query))
      && (statusFilter === "all" || business.status === statusFilter);
  }), [data, searchQuery, statusFilter]);

  const tabs: { id: Tab; label: string; icon: typeof Activity }[] = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "businesses", label: "Businesses", icon: Building2 },
    { id: "system", label: "System Health", icon: Cpu },
    { id: "activity", label: "Activity Log", icon: Shield },
  ];

  return (
    <div className="min-h-screen bg-background pt-[60px] text-foreground transition-colors">
      <main className="mx-auto max-w-[1280px] px-6 py-8">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="mb-1 flex items-center gap-2 text-accent">
              <Shield size={18} />
              <span className="text-xs font-bold uppercase tracking-widest">Super Admin</span>
            </div>
            <h1 className="text-2xl font-black">HaqDesk AI Control Center</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">Platform-wide businesses, users, and service health</p>
          </div>
          <button onClick={() => void loadDashboard()} disabled={loading} className="ds-button ds-button-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </header>

        <nav className="mb-8 flex gap-1 overflow-x-auto border-b border-border" aria-label="Dashboard sections">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveTab(id)}
              className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium ${
                activeTab === id ? "border-accent text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}>
              <Icon size={14} /> {label}
            </button>
          ))}
        </nav>

        {error && <div role="alert" className="mb-6 rounded-xl border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-sm text-[var(--error-foreground)]">{error}</div>}
        {loading && !data && <div className="py-20 text-center text-muted-foreground">Loading live platform data…</div>}

        {data && activeTab === "overview" && (
          <>
            <section className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-3" aria-label="Platform statistics">
              {data.stats.map((stat) => {
                const Icon = statIcons[stat.key] ?? Activity;
                return <article key={stat.key} className="ds-card p-5">
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-[color-mix(in_srgb,var(--accent)_12%,transparent)] text-accent"><Icon size={18} /></div>
                  <p className="text-2xl font-black text-foreground">{stat.value.toLocaleString()}</p>
                  <p className="text-xs font-medium text-muted-foreground">{stat.label}</p>
                  <p className="mt-1 text-[11px] text-[var(--success-foreground)]">{stat.change}</p>
                </article>;
              })}
            </section>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <section className="ds-card p-6">
                <h2 className="mb-4 text-sm font-bold">Top Businesses by Messages</h2>
                <div className="space-y-3">
                  {[...data.businesses].sort((a, b) => b.messages - a.messages).slice(0, 5).map((business) => (
                    <div key={business.id} className="flex items-center justify-between rounded-xl bg-surface-wash p-3">
                      <div><p className="text-sm font-semibold">{business.name}</p><p className="text-xs text-muted-foreground">{business.agents} agents</p></div>
                      <span className="text-sm font-bold">{business.messages.toLocaleString()}</span>
                    </div>
                  ))}
                  {!data.businesses.length && <p className="text-sm text-muted-foreground">No businesses yet.</p>}
                </div>
              </section>
              <ActivityList items={data.recent_activity.slice(0, 5)} title="Recent Platform Activity" />
            </div>
          </>
        )}

        {data && activeTab === "businesses" && (
          <section className="ds-card overflow-hidden">
            <div className="flex flex-wrap gap-3 border-b border-border p-4">
              <label className="relative flex-1">
                <span className="sr-only">Search businesses</span><Search size={14} className="absolute left-3 top-3.5 text-muted-foreground" />
                <input className="ds-input pl-9" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search businesses or owners…" />
              </label>
              <select className="ds-input w-auto" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-left text-sm">
              <thead className="bg-surface-wash text-xs text-muted-foreground"><tr>
                <th className="p-4">Business</th><th className="p-4">Owner</th><th className="p-4">Status</th>
                <th className="p-4">Messages</th><th className="p-4">Agents</th><th className="p-4">Joined</th>
              </tr></thead>
              <tbody className="divide-y divide-border">{filteredBusinesses.map((business) => <tr key={business.id}>
                <td className="p-4 font-semibold">{business.name}</td><td className="p-4 text-muted-foreground">{business.owner}</td>
                <td className="p-4"><span className="rounded-full bg-surface-wash px-2 py-1 text-xs">{business.status}</span></td>
                <td className="p-4">{business.messages.toLocaleString()}</td><td className="p-4">{business.agents}</td>
                <td className="p-4 text-muted-foreground">{business.joined ? new Date(business.joined).toLocaleDateString() : "—"}</td>
              </tr>)}</tbody>
            </table></div>
            <p className="p-4 text-xs text-muted-foreground">{filteredBusinesses.length} businesses found</p>
          </section>
        )}

        {data && activeTab === "system" && <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="ds-card p-6"><h2 className="mb-5 flex items-center gap-2 text-sm font-bold"><Cpu size={14} className="text-accent" />Service Status</h2>
            <div className="space-y-3">{data.system_health.map((service) => <div key={service.label} className="flex justify-between rounded-xl bg-surface-wash p-3">
              <span className="text-sm font-medium">{service.label}</span><span className="text-xs text-[var(--success-foreground)]">{service.status} · {service.detail}</span>
            </div>)}</div>
          </section>
          <section className="ds-card p-6"><h2 className="mb-5 flex items-center gap-2 text-sm font-bold"><Database size={14} className="text-accent" />Database Stats</h2>
            <dl className="space-y-3">{data.database_stats.map((item) => <div key={item.label} className="flex justify-between border-b border-border pb-3">
              <dt className="text-sm text-muted-foreground">{item.label}</dt><dd className="font-bold">{item.value.toLocaleString()}</dd>
            </div>)}</dl>
          </section>
        </div>}

        {data && activeTab === "activity" && <ActivityList items={data.recent_activity} title="Platform Activity Log" />}
      </main>
    </div>
  );
}

function ActivityList({ items, title }: { items: ActivityItem[]; title: string }) {
  return <section className="ds-card p-6"><h2 className="mb-4 text-sm font-bold">{title}</h2>
    <div className="divide-y divide-border">{items.map((item, index) => <div key={`${item.action}-${item.timestamp}-${index}`} className="flex items-center gap-3 py-3">
      <span className={`h-2 w-2 rounded-full ${item.type === "success" ? "bg-[var(--success)]" : "bg-accent"}`} />
      <div className="min-w-0 flex-1"><p className="truncate text-sm">{item.action}</p><p className="truncate text-xs text-muted-foreground">{item.target}</p></div>
      <time className="text-xs text-muted-foreground">{relativeTime(item.timestamp)}</time>
    </div>)}
    {!items.length && <p className="text-sm text-muted-foreground">No recent activity.</p>}</div>
  </section>;
}
