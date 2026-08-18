"use client";

import { useMemo, useState } from "react";
import { ArrowUpDown, Facebook, Info, Instagram, Mail } from "lucide-react";
import type { MetricValue, PlatformAnalytics, PlatformAnalyticsItem } from "../types";

const COLORS: Record<string, string> = { facebook: "#6D4AE2", instagram: "#818CF8", email: "#F59E0B" };
const icons = { facebook: Facebook, instagram: Instagram, email: Mail };
const TYPICAL_TOOLTIP = "The middle response time. Half of responses were faster and half were slower.";
const NINETY_TOOLTIP = "90% of customer conversations received a first response within this time. The slowest 10% took longer.";

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "Not Available Yet";
  if (seconds < 60) return `${Math.round(seconds)} sec`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  return `${hours} hr${minutes ? ` ${minutes} min` : ""}`;
}

const number = (metric: MetricValue) => metric.value?.toLocaleString() ?? "-";
const activeConversations = (item: PlatformAnalyticsItem) => (item.open_conversations.value || 0) + (item.pending_conversations.value || 0);
const negativeSummary = (item: PlatformAnalyticsItem) => `${number(item.negative_messages)} negative messages — ${item.negative_sentiment_rate.value ?? 0}% of analyzed customer messages`;
const businessText = (value: string) => value
  .replace(/\bpartial\b/gi, "limited")
  .replace(/unresolved backlog/gi, "open support workload")
  .replace(/canonicalization/gi, "customer matching");

type BarValue = { name: string; value: number; color: string; display?: string; tooltip?: string };
function ComparisonBars({ title, rows }: { title: string; rows: { label: string; values: BarValue[] }[] }) {
  const max = Math.max(1, ...rows.flatMap((row) => row.values.map((value) => value.value)));
  return <section className="rounded-3xl border border-border bg-surface p-6 shadow-sm">
    <h3 className="text-sm font-extrabold !text-foreground">{title}</h3>
    <div className="mt-5 space-y-5">{rows.map((row) => <div key={row.label}>
      <p className="mb-2 text-xs font-bold text-muted-foreground">{row.label}</p>
      <div className="space-y-1.5">{row.values.map((value) => <div key={value.name} className="flex items-center gap-2">
        <span className="w-24 text-[10px] text-muted-foreground">{value.name}</span>
        <div className="h-3 flex-1 rounded-full bg-surface-wash"><div title={value.tooltip} aria-label={`${row.label} ${value.name}: ${value.tooltip ?? value.display ?? value.value}`} className="h-3 rounded-full" style={{ width: `${value.value / max * 100}%`, backgroundColor: value.color }} /></div>
        <span className="w-20 text-right text-xs font-bold text-foreground">{value.display ?? value.value}</span>
      </div>)}</div>
    </div>)}</div>
  </section>;
}

function HelpLabel({ children, tooltip }: { children: string; tooltip: string }) {
  return <span title={tooltip} className="inline-flex items-center gap-1">{children}<Info aria-label={tooltip} size={11} className="shrink-0 cursor-help" /></span>;
}

export function responseSampleText(sampleSize: number): string {
  return `Based on ${sampleSize} answered conversation${sampleSize === 1 ? "" : "s"}`;
}

function ResponseMetric({ metric }: { metric: MetricValue }) {
  const sampleSize = metric.sample_size || 0;
  return <div>
    <p className="font-bold">{sampleSize === 0 ? "Not Available Yet" : formatDuration(metric.value)}</p>
    {sampleSize > 0 && <p className="mt-0.5 text-[10px] text-muted-foreground">{responseSampleText(sampleSize)}</p>}
    {sampleSize > 0 && sampleSize < 5 && <span className="mt-1 inline-flex rounded-full bg-[var(--warning-surface)] px-2 py-0.5 text-[9px] font-bold text-[var(--warning)]">Limited Data</span>}
  </div>;
}

export function formatPeakTime(weekday: string | null, hour: number | null): string {
  if (!weekday || hour === null) return "Not Available Yet";
  const day = weekday.charAt(0).toUpperCase() + weekday.slice(1);
  const time = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: "UTC" }).format(new Date(Date.UTC(2026, 0, 1, hour)));
  return `${day} at ${time}`;
}

export default function PlatformAnalyticsSection({ data, filteredPlatform }: { data: PlatformAnalytics; filteredPlatform: string }) {
  const [sortKey, setSortKey] = useState<"platform" | "conversations" | "customerMessages" | "businessReplies" | "backlog" | "negative" | "response">("conversations");
  const [descending, setDescending] = useState(true);
  const platforms = useMemo(() => [...data.platforms].sort((a, b) => {
    const values = (item: PlatformAnalyticsItem) => ({
      platform: item.display_name, conversations: item.conversations.value || 0,
      customerMessages: item.inbound_messages.value || 0, businessReplies: item.outgoing_messages.value || 0,
      backlog: activeConversations(item), negative: item.negative_sentiment_rate.value || 0,
      response: item.median_first_response_seconds.value ?? Number.MAX_SAFE_INTEGER,
    });
    const left = values(a)[sortKey]; const right = values(b)[sortKey];
    const result = typeof left === "string" ? left.localeCompare(String(right)) : Number(left) - Number(right);
    return descending ? -result : result;
  }), [data.platforms, descending, sortKey]);
  const sort = (key: typeof sortKey) => { if (key === sortKey) setDescending((value) => !value); else { setSortKey(key); setDescending(true); } };

  return <section className="space-y-6 rounded-[2rem] bg-background p-4 text-foreground sm:p-6" aria-labelledby="channel-performance-title">
    <div>
      <h2 id="channel-performance-title" className="text-2xl font-black !text-foreground">Channel Performance</h2>
      <p className="mt-1 text-sm text-muted-foreground">Compare customer demand, open support work, and response speed by channel. High activity may represent engagement, inquiries, complaints, or service problems.</p>
      {filteredPlatform && <p className="mt-2 inline-flex rounded-full bg-accent/10 px-3 py-1 text-xs font-bold text-accent">Filtered to {filteredPlatform}; other channels are intentionally hidden.</p>}
      <div className="mt-3 flex gap-2 rounded-2xl border border-accent/20 bg-accent/10 p-3 text-xs text-foreground"><Info size={15} className="mt-0.5 shrink-0 text-accent" /><p>New conversations are counted using the conversation creation date. Messages are counted using the message date. A platform may therefore have messages during the selected period even when no new conversation was created.</p></div>
    </div>

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{platforms.map((item) => {
      const Icon = icons[item.platform as keyof typeof icons] || Mail;
      return <article key={item.platform} className="rounded-3xl border border-border bg-surface p-5 shadow-sm">
        <div className="flex items-center justify-between"><div className="flex items-center gap-2"><Icon size={18} style={{ color: COLORS[item.platform] }} /><h3 className="font-black !text-foreground">{item.display_name}</h3></div><span className={`rounded-full px-2 py-1 text-[10px] font-bold ${item.is_connected ? "bg-[var(--success-surface)] text-[var(--success-foreground)]" : "bg-[var(--warning-surface)] text-[var(--warning)]"}`}>{item.is_connected ? "Connected" : "Past activity only"}</span></div>
        <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-xs text-muted-foreground">New Conversations</dt><dd className="text-xl font-black">{number(item.conversations)}</dd></div>
          <div><dt className="text-xs text-muted-foreground"><HelpLabel tooltip="Conversations currently marked open or pending. This is a current snapshot and may include conversations created before the selected period.">Currently Open Conversations</HelpLabel></dt><dd className="text-xl font-black">{activeConversations(item)}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Customer Messages</dt><dd className="font-bold">{number(item.inbound_messages)}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Business Replies</dt><dd className="font-bold">{number(item.outgoing_messages)}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Customers</dt><dd className="font-bold">{number(item.unique_customers)}</dd></div>
          <div><dt className="text-xs text-muted-foreground">Open Support Workload</dt><dd className="font-bold">{activeConversations(item)}</dd></div>
          <div><dt className="text-xs text-muted-foreground"><HelpLabel tooltip={TYPICAL_TOOLTIP}>Typical Response Time</HelpLabel></dt><dd><ResponseMetric metric={item.median_first_response_seconds} /></dd></div>
          <div><dt className="text-xs text-muted-foreground"><HelpLabel tooltip={NINETY_TOOLTIP}>90% Responded Within</HelpLabel></dt><dd><ResponseMetric metric={item.p90_first_response_seconds} /></dd></div>
          <div className="col-span-2"><dt className="text-xs text-muted-foreground">Negative Customer Messages</dt><dd className="font-bold">{negativeSummary(item)}</dd></div>
        </dl>
      </article>;
    })}</div>

    <div className="border-t border-border pt-2">
      <h3 className="text-xl font-black !text-foreground">Channel Comparison Charts</h3>
      <p className="mt-1 text-sm text-muted-foreground">Compare conversation volume, customer messages, response speed, and sentiment across channels.</p>
    </div>
    <div className="grid gap-6 lg:grid-cols-2">
      <ComparisonBars title="Conversations by Platform" rows={platforms.map((item) => ({ label: item.display_name, values: [{ name: "Conversations", value: Number(item.conversations.value || 0), color: COLORS[item.platform] }] }))} />
      <ComparisonBars title="Customer Messages and Business Replies" rows={platforms.map((item) => ({ label: item.display_name, values: [{ name: "Customer", value: Number(item.inbound_messages.value || 0), color: "#6D4AE2" }, { name: "Replies", value: Number(item.outgoing_messages.value || 0), color: "#10B981" }] }))} />
    </div>
    <div className="grid gap-6 lg:grid-cols-3">
      <ComparisonBars title="Share of Conversations (%)" rows={platforms.map((item) => ({ label: item.display_name, values: [{ name: "Share", value: Number(item.conversation_share_percentage.value || 0), color: COLORS[item.platform] }] }))} />
      <ComparisonBars title="Response Time" rows={platforms.map((item) => ({ label: item.display_name, values: [{ name: "Typical", value: Number(item.median_first_response_seconds.value || 0), display: item.median_first_response_seconds.sample_size ? formatDuration(item.median_first_response_seconds.value) : "Not Available Yet", tooltip: `${item.median_first_response_seconds.sample_size ? formatDuration(item.median_first_response_seconds.value) : "Not Available Yet"}. ${responseSampleText(item.median_first_response_seconds.sample_size || 0)}`, color: "#10B981" }, { name: "90% Within", value: Number(item.p90_first_response_seconds.value || 0), display: item.p90_first_response_seconds.sample_size ? formatDuration(item.p90_first_response_seconds.value) : "Not Available Yet", tooltip: `${item.p90_first_response_seconds.sample_size ? formatDuration(item.p90_first_response_seconds.value) : "Not Available Yet"}. ${responseSampleText(item.p90_first_response_seconds.sample_size || 0)}`, color: "#F59E0B" }] }))} />
      <ComparisonBars title="Customer Sentiment" rows={platforms.map((item) => ({ label: item.display_name, values: [{ name: "Positive", value: Number(item.positive_messages.value || 0), color: "#10B981" }, { name: "Neutral", value: Number(item.neutral_messages.value || 0), color: "#818CF8" }, { name: "Negative", value: Number(item.negative_messages.value || 0), color: "#EF4444" }, { name: "Not Yet Analyzed", value: Number(item.unclassified_messages.value || 0), color: "#94A3B8" }] }))} />
    </div>

    <div className="border-t border-border pt-2">
      <h3 className="text-xl font-black !text-foreground">Detailed Channel Breakdown</h3>
      <p className="mt-1 text-sm text-muted-foreground">Review all channel metrics together and sort the table by the measure that matters most.</p>
    </div>
    <p className="text-xs font-semibold text-muted-foreground">Times shown in {data.applied_filters.timezone === "Asia/Kathmandu" ? "Kathmandu time" : data.applied_filters.timezone}.</p>
    <section className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"><div className="overflow-x-auto"><table className="min-w-[1300px] w-full text-left text-xs">
      <thead className="bg-surface-wash text-muted-foreground"><tr>{[["platform","Platform"],["conversations","New Conversations"],["customerMessages","Customer Messages"],["businessReplies","Business Replies"],["backlog","Open Support Workload"],["negative","Negative Customer Messages"],["response","Typical Response Time"]].map(([key,label]) => <th key={key} className="px-4 py-3"><button className="inline-flex items-center gap-1 font-bold" onClick={() => sort(key as typeof sortKey)}>{label}<ArrowUpDown size={12} /></button></th>)}<th className="px-4 py-3">Connected</th><th className="px-4 py-3">Customers</th><th className="px-4 py-3"><HelpLabel tooltip={NINETY_TOOLTIP}>90% Responded Within</HelpLabel></th><th className="px-4 py-3">Busiest Time</th></tr></thead>
      <tbody>{platforms.map((item) => <tr key={item.platform} className="border-t border-border"><td className="px-4 py-3 font-bold">{item.display_name}</td><td className="px-4 py-3">{number(item.conversations)}</td><td className="px-4 py-3">{number(item.inbound_messages)}</td><td className="px-4 py-3">{number(item.outgoing_messages)}</td><td className="px-4 py-3">{activeConversations(item)}</td><td className="px-4 py-3">{negativeSummary(item)}</td><td className="px-4 py-3"><ResponseMetric metric={item.median_first_response_seconds} /></td><td className="px-4 py-3">{item.is_connected ? "Yes" : "No"}</td><td className="px-4 py-3">{number(item.unique_customers)}</td><td className="px-4 py-3"><ResponseMetric metric={item.p90_first_response_seconds} /></td><td className="px-4 py-3">{formatPeakTime(item.peak_weekday, item.peak_hour)}</td></tr>)}</tbody>
    </table></div></section>

    {data.insights.length > 0 && <section className="rounded-3xl border border-accent/20 bg-accent/5 p-5"><h3 className="font-black text-accent">Business Insights</h3><ul className="mt-3 space-y-2 text-sm text-foreground">{data.insights.map((insight) => <li key={insight}>• {businessText(insight)}</li>)}</ul></section>}
    {data.data_quality.length > 0 && <section className="rounded-3xl border border-[var(--warning-border)] bg-[var(--warning-surface)] p-5"><h3 className="font-black text-[var(--warning)]">About This Data</h3><ul className="mt-2 space-y-1 text-xs text-[var(--warning)]">{data.data_quality.map((notice, index) => <li key={`${notice.metric}-${index}`}>{businessText(notice.message)}</li>)}</ul></section>}
  </section>;
}
