import Link from "next/link";
import { AlertTriangle, ArrowRight, BarChart3, Clock3, MessageCircleMore, Radio, ShieldAlert, UsersRound } from "lucide-react";
import MessageVolumeChart from "./MessageVolumeChart";
import type { AnalyticsSummary, CustomerAttentionResponse, CustomerSummary, MessageTrend, MetricValue, PlatformAnalytics, PlatformAnalyticsItem } from "../types";

type Role = "business_admin" | "supervisor";

type OperationsOverviewProps = {
  summary: AnalyticsSummary;
  trend: MessageTrend;
  platforms: PlatformAnalytics;
  customerSummary: CustomerSummary;
  attention: CustomerAttentionResponse;
  role: Role;
};

const metricValue = (metric?: MetricValue) => metric?.value ?? 0;
const compact = (value: number) => value.toLocaleString();

function responseTime(seconds: number | null) {
  if (seconds === null) return "Not available";
  if (seconds < 60) return `${Math.round(seconds)} sec`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} hr ${minutes % 60 ? `${minutes % 60} min` : ""}`.trim();
}

function channelHealth(platform: PlatformAnalyticsItem) {
  const open = metricValue(platform.open_conversations) + metricValue(platform.pending_conversations);
  const waiting = metricValue(platform.unanswered_conversations);
  const negative = metricValue(platform.negative_messages);
  if (waiting > 0 || open > 0 || negative > 0) return { label: "Needs attention", tone: "text-[var(--warning)] bg-[var(--warning-surface)]" };
  return { label: "On track", tone: "text-[var(--success-foreground)] bg-[var(--success-surface)]" };
}

export function OperationsOverview({ summary, trend, platforms, customerSummary, attention, role }: OperationsOverviewProps) {
  const openWork = metricValue(summary.metrics.open_conversations) + metricValue(summary.metrics.pending_conversations);
  const waiting = metricValue(customerSummary.metrics.customers_waiting_for_reply);
  const negative = Object.values(summary.sentiment_distribution).length
    ? summary.sentiment_distribution.negative || 0
    : platforms.platforms.reduce((total, platform) => total + metricValue(platform.negative_messages), 0);
  const topChannel = [...platforms.platforms].sort((a, b) => metricValue(b.conversations) - metricValue(a.conversations))[0];
  const visibleChannels = [...platforms.platforms].sort((a, b) => metricValue(b.conversations) - metricValue(a.conversations)).slice(0, 4);
  const attentionCustomers = attention.customers.slice(0, 5);
  const metrics = [
    { label: "Open workload", value: compact(openWork), detail: openWork ? "Conversations that still need a decision" : "No unresolved conversations", icon: MessageCircleMore, tone: "text-accent-glow bg-accent/10" },
    { label: "Customers waiting", value: compact(waiting), detail: "Waiting for your team to reply", icon: Clock3, tone: "text-[var(--warning)] bg-[var(--warning-surface)]" },
    { label: "Negative signals", value: compact(negative), detail: "Customer messages marked negative", icon: AlertTriangle, tone: "text-[var(--error-foreground)] bg-[var(--error-surface)]" },
    { label: "Top demand channel", value: topChannel?.display_name || "No data", detail: topChannel ? `${compact(metricValue(topChannel.conversations))} conversations in this period` : "Connect a channel to begin", icon: Radio, tone: "text-blue-600 bg-blue-500/10" },
  ];

  return <div className="space-y-6">
    <section className="rounded-[2rem] border border-surface-border bg-gradient-to-br from-surface via-surface to-accent/5 p-6 sm:p-7">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl"><p className="text-[10px] font-black uppercase tracking-[0.24em] text-accent-glow">{role === "supervisor" ? "Team command center" : "Support operations"}</p>
          <h2 className="mt-2 font-heading text-3xl font-black tracking-tight text-foreground sm:text-4xl">Know where support needs your attention.</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">Start with workload, customer waits, and channel demand. Every number below is scoped to the filters you selected.</p>
        </div>
        <Link href="/inbox" className="ds-button ds-button-primary shrink-0">Open priority inbox <ArrowRight size={15} /></Link>
      </div>
    </section>

    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map(({ label, value, detail, icon: Icon, tone }) => <article key={label} className="rounded-2xl border border-surface-border bg-surface p-5 shadow-sm">
        <div className="mb-5 flex items-start justify-between"><div className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone}`}><Icon size={18} /></div></div>
        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
        <p className="mt-1 truncate font-heading text-3xl font-black tracking-tight text-foreground" title={value}>{value}</p>
        <p className="mt-2 min-h-8 text-xs leading-4 text-muted-foreground">{detail}</p>
      </article>)}
    </div>

    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.85fr)]">
      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6">
        <div className="mb-5 flex items-start justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Channel decisions</p><h3 className="mt-1 text-xl font-black tracking-tight">Where customers are asking for help</h3></div><Link href="/analytics?view=channels" className="text-xs font-bold text-accent-glow hover:underline">Full channel view</Link></div>
        {!visibleChannels.length ? <EmptyPanel label="No channel activity for this period" /> : <div className="divide-y divide-surface-border">{visibleChannels.map((platform) => {
          const health = channelHealth(platform);
          return <div key={platform.platform} className="grid gap-3 py-4 first:pt-0 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center">
            <div><div className="flex items-center gap-2"><p className="font-bold text-foreground">{platform.display_name}</p><span className={`rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${health.tone}`}>{health.label}</span></div>
              <p className="mt-1 text-xs text-muted-foreground">{compact(metricValue(platform.conversations))} conversations · {compact(metricValue(platform.unanswered_conversations))} waiting for a reply</p></div>
            <div className="text-left sm:text-right"><p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Typical first reply</p><p className="mt-1 text-sm font-black text-foreground">{responseTime(platform.median_first_response_seconds.value)}</p></div>
            <Link href="/inbox" className="inline-flex items-center gap-1 text-xs font-bold text-accent-glow hover:underline">Review <ArrowRight size={13} /></Link>
          </div>;
        })}</div>}
      </section>

      <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6">
        <div className="mb-5 flex items-start justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Customer attention</p><h3 className="mt-1 text-xl font-black tracking-tight">Who needs a response</h3></div><ShieldAlert size={19} className="text-[var(--warning)]" /></div>
        {!attentionCustomers.length ? <EmptyPanel label="No customers need attention right now" /> : <div className="space-y-3">{attentionCustomers.map((customer) => <Link key={customer.customer_id} href="/inbox" className="block rounded-2xl border border-surface-border p-3 transition hover:border-accent/30 hover:bg-surface-wash">
          <div className="flex gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent/10 text-xs font-black text-accent-glow">{customer.display_name.charAt(0).toUpperCase()}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-bold">{customer.display_name}</p><span className="text-[10px] font-black text-[var(--warning)]">{Math.round(customer.attention_score)}/100</span></div><p className="mt-1 line-clamp-1 text-[11px] text-muted-foreground">{customer.primary_reasons[0] || "Needs a support review"}</p></div></div>
        </Link>)}</div>}
      </section>
    </div>

    <section><div className="mb-3 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Demand over time</p><h3 className="mt-1 text-xl font-black tracking-tight">Conversation activity</h3></div><Link href="/analytics?view=trends" className="text-xs font-bold text-accent-glow hover:underline">Explore trend</Link></div><MessageVolumeChart trend={trend} /></section>
  </div>;
}

export function GrowthInsights({ platforms, customerSummary, summary }: Pick<OperationsOverviewProps, "platforms" | "customerSummary" | "summary">) {
  const ranked = [...platforms.platforms].sort((a, b) => metricValue(b.conversations) - metricValue(a.conversations));
  const busiest = ranked[0];
  const slowest = [...platforms.platforms].filter((item) => item.median_first_response_seconds.value !== null).sort((a, b) => (b.median_first_response_seconds.value || 0) - (a.median_first_response_seconds.value || 0))[0];
  const mostNegative = [...platforms.platforms].sort((a, b) => metricValue(b.negative_sentiment_rate) - metricValue(a.negative_sentiment_rate))[0];
  const repeatCustomers = metricValue(customerSummary.metrics.repeat_contact_customers);
  const strategicCards = [
    { title: "Protect the busiest channel", value: busiest?.display_name || "No demand signal yet", detail: busiest ? `${compact(metricValue(busiest.conversations))} conversations came through this channel. Plan coverage around its busiest hours.` : "Connect a support channel to identify demand.", icon: Radio },
    { title: "Reduce response friction", value: slowest ? `${slowest.display_name}: ${responseTime(slowest.median_first_response_seconds.value)}` : "Response data is still building", detail: slowest ? `${compact(metricValue(slowest.unanswered_conversations))} conversations have no business reply in this period.` : "Reply timestamps are needed before response recommendations are available.", icon: Clock3 },
    { title: "Recover at-risk customers", value: mostNegative ? `${metricValue(mostNegative.negative_sentiment_rate)}% negative on ${mostNegative.display_name}` : "No sentiment signal yet", detail: mostNegative ? "Review the themes in negative messages and turn recurring questions into knowledge content." : "Sentiment needs analysed customer messages.", icon: AlertTriangle },
    { title: "Turn repeat contacts into clarity", value: `${compact(repeatCustomers)} repeat-contact customers`, detail: "Repeated questions often reveal unclear policies, delivery updates, or product information. Use these conversations to prioritise self-service content.", icon: UsersRound },
  ];
  const demand = metricValue(summary.metrics.customer_messages);

  return <div className="space-y-6">
    <section className="rounded-[2rem] border border-accent/20 bg-gradient-to-br from-accent/10 via-surface to-blue-500/5 p-6 sm:p-8"><p className="text-[10px] font-black uppercase tracking-[0.24em] text-accent-glow">Admin growth insights</p><h2 className="mt-2 max-w-2xl font-heading text-3xl font-black tracking-tight sm:text-4xl">Use support demand to make better business decisions.</h2><p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">This view turns conversation data into practical next actions for staffing, channel investment, and customer experience. It does not estimate revenue until sales or order data is connected.</p><div className="mt-6 flex items-center gap-3 text-sm font-bold text-foreground"><BarChart3 size={17} className="text-accent-glow" />{compact(demand)} customer messages in the selected period</div></section>
    <div className="grid gap-4 md:grid-cols-2">{strategicCards.map(({ title, value, detail, icon: Icon }) => <article key={title} className="rounded-[1.75rem] border border-surface-border bg-surface p-6 shadow-sm"><Icon size={19} className="mb-5 text-accent-glow" /><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">{title}</p><h3 className="mt-2 text-xl font-black tracking-tight">{value}</h3><p className="mt-3 text-sm leading-6 text-muted-foreground">{detail}</p></article>)}</div>
    <section className="rounded-2xl border border-surface-border bg-surface-wash p-5 text-sm text-muted-foreground"><strong className="text-foreground">Important:</strong> support analytics can show demand, wait time, sentiment, and repeat contact. Connect orders, conversion events, or CRM data before making revenue or ROI claims.</section>
  </div>;
}

function EmptyPanel({ label }: { label: string }) { return <div className="flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-surface-border bg-surface-wash px-4 text-center text-sm text-muted-foreground">{label}</div>; }
export function ChannelDecisionView({ platforms }: { platforms: PlatformAnalytics }) {
  const rows = [...platforms.platforms].sort((a, b) => metricValue(b.conversations) - metricValue(a.conversations));
  const total = rows.reduce((sum, item) => sum + metricValue(item.conversations), 0);

  return <div className="space-y-6">
    <section className="rounded-[2rem] border border-surface-border bg-surface p-6 sm:p-8"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">Channel performance</p><h2 className="mt-2 font-heading text-3xl font-black tracking-tight">Decide where your team should focus.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">Compare incoming demand, unresolved work, response pace, and customer sentiment without leaving the decision context.</p></section>
    {!rows.length ? <EmptyPanel label="No channel activity for these filters" /> : <section className="overflow-hidden rounded-[2rem] border border-surface-border bg-surface"><div className="grid grid-cols-[minmax(150px,1.3fr)_0.8fr_0.8fr_0.8fr] gap-3 border-b border-surface-border bg-surface-wash px-5 py-3 text-[9px] font-black uppercase tracking-[0.16em] text-muted-foreground sm:px-6"><span>Channel</span><span>Demand</span><span>Open work</span><span>Response pace</span></div>{rows.map((platform) => {
      const conversationCount = metricValue(platform.conversations);
      const open = metricValue(platform.open_conversations) + metricValue(platform.pending_conversations);
      const share = total ? Math.round((conversationCount / total) * 100) : 0;
      const health = channelHealth(platform);
      return <article key={platform.platform} className="grid grid-cols-[minmax(150px,1.3fr)_0.8fr_0.8fr_0.8fr] gap-3 border-b border-surface-border px-5 py-5 last:border-none sm:px-6"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="truncate text-sm font-black">{platform.display_name}</h3><span className={`rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${health.tone}`}>{health.label}</span></div><p className="mt-1 text-[11px] text-muted-foreground">{platform.is_connected ? "Connected" : "Not currently connected"}</p></div><div><p className="text-sm font-black">{compact(conversationCount)}</p><p className="mt-1 text-[10px] text-muted-foreground">{share}% of all conversations</p></div><div><p className="text-sm font-black">{compact(open)}</p><p className="mt-1 text-[10px] text-muted-foreground">{compact(metricValue(platform.unanswered_conversations))} unanswered</p></div><div><p className="text-sm font-black">{responseTime(platform.median_first_response_seconds.value)}</p><p className="mt-1 text-[10px] text-muted-foreground">{metricValue(platform.negative_sentiment_rate)}% negative</p></div></article>;
    })}</section>}
    <section className="rounded-2xl border border-surface-border bg-surface-wash p-5 text-sm text-muted-foreground">Response pace uses the median first response time, which is less affected by an occasional unusually slow reply. Sentiment information is based only on customer messages that have been analysed.</section>
  </div>;
}

export function CustomerDecisionView({ customerSummary: summary, attention }: Pick<OperationsOverviewProps, "customerSummary" | "attention">) {
  const snapshots = [
    ["Customers needing attention", metricValue(summary.metrics.customers_needing_attention), "Review conversations with unanswered messages, urgent priority, or repeated contact."],
    ["Waiting for a reply", metricValue(summary.metrics.customers_waiting_for_reply), "Customers whose latest conversation is waiting for a business response."],
    ["Repeat contact customers", metricValue(summary.metrics.repeat_contact_customers), "Customers returning quickly may point to an unclear answer or unresolved issue."],
    ["New customers", metricValue(summary.metrics.new_customers), "A useful signal for onboarding, campaign, or launch demand."],
  ] as const;

  return <div className="space-y-6"><section className="rounded-[2rem] border border-surface-border bg-surface p-6 sm:p-8"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">Customer experience</p><h2 className="mt-2 font-heading text-3xl font-black tracking-tight">Focus on the customers who need help first.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">The attention score prioritises unresolved work, waiting time, urgent conversations, negative messages, and repeat contacts.</p></section><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{snapshots.map(([label, value, detail]) => <article key={label} className="rounded-2xl border border-surface-border bg-surface p-5"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</p><p className="mt-2 font-heading text-3xl font-black tracking-tight">{compact(value)}</p><p className="mt-3 text-xs leading-5 text-muted-foreground">{detail}</p></article>)}</div><section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Priority follow-up</p><h3 className="mt-1 text-xl font-black tracking-tight">Customers needing attention</h3></div><Link href="/inbox" className="text-xs font-bold text-accent-glow hover:underline">Open inbox</Link></div>{!attention.customers.length ? <EmptyPanel label="No customers need attention for these filters" /> : <div className="grid gap-3 md:grid-cols-2">{attention.customers.slice(0, 10).map((customer) => <Link key={customer.customer_id} href="/inbox" className="rounded-2xl border border-surface-border p-4 transition hover:border-accent/30 hover:bg-surface-wash"><div className="flex gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{customer.display_name.charAt(0).toUpperCase()}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><h4 className="truncate text-sm font-black">{customer.display_name}</h4><span className="text-xs font-black text-[var(--warning)]">{Math.round(customer.attention_score)}</span></div><p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">{customer.primary_reasons.join(" · ") || "Needs an operational review"}</p><div className="mt-3 flex flex-wrap gap-2 text-[10px] font-bold text-muted-foreground"><span>{customer.waiting_conversation_count} waiting</span><span>{customer.repeat_contact_count} repeat contacts</span><span>{customer.negative_customer_message_count} negative</span></div></div></div></Link>)}</div>}</section></div>;
}

export function TeamOperationsView({ summary, platforms, agentOptions }: { summary: AnalyticsSummary; platforms: PlatformAnalytics; agentOptions: { id: number; name: string; email: string }[] }) {
  const unassigned = platforms.platforms.reduce((total, item) => total + metricValue(item.unassigned_conversations), 0);
  const priority = platforms.platforms.reduce((total, item) => total + metricValue(item.high_priority_conversations) + metricValue(item.urgent_priority_conversations), 0);
  const metrics = [["Team members", metricValue(summary.metrics.team_members)], ["Unassigned conversations", unassigned], ["High-priority workload", priority], ["Business replies", metricValue(summary.metrics.agent_messages)]] as const;
  return <div className="space-y-6"><section className="rounded-[2rem] border border-surface-border bg-surface p-6 sm:p-8"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">Team operations</p><h2 className="mt-2 font-heading text-3xl font-black tracking-tight">Keep coverage aligned with demand.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">Use this operational view to route unassigned work, balance channel coverage, and see when priority queues need help.</p></section><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value]) => <article key={label} className="rounded-2xl border border-surface-border bg-surface p-5"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</p><p className="mt-2 font-heading text-3xl font-black tracking-tight">{compact(value)}</p></article>)}</div><section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-6"><div className="mb-5 flex items-end justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Available team</p><h3 className="mt-1 text-xl font-black tracking-tight">Team directory</h3></div><Link href="/team" className="text-xs font-bold text-accent-glow hover:underline">Manage team</Link></div>{!agentOptions.length ? <EmptyPanel label="No team members are available to display" /> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{agentOptions.map((agent) => <div key={agent.id} className="flex items-center gap-3 rounded-2xl border border-surface-border p-4"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/10 text-sm font-black text-accent-glow">{(agent.name || agent.email).charAt(0).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-sm font-bold">{agent.name || agent.email}</p><p className="truncate text-[11px] text-muted-foreground">{agent.email}</p></div></div>)}</div>}</section><section className="rounded-2xl border border-surface-border bg-surface-wash p-5 text-sm leading-6 text-muted-foreground"><strong className="text-foreground">Data note:</strong> individual quality and response-time scores should only be shown when assignment and ownership history are recorded. This dashboard intentionally shows verified team-wide operational data rather than guessing agent performance.</section></div>;
}