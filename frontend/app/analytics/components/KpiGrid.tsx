import { CircleAlert, MessageCircleMore, MessagesSquare, MessageSquareText, Reply, Sparkles, UserRoundCheck, Users } from "lucide-react";
import type { AnalyticsSummary } from "../types";
import KpiCard from "./KpiCard";

export default function KpiGrid({ summary }: { summary: AnalyticsSummary }) {
  const comparisonDays = Math.max(1, Math.round((new Date(summary.applied_filters.to).getTime() - new Date(summary.applied_filters.from).getTime()) / 86_400_000));
  const currentFrom = new Date(summary.applied_filters.from);
  const previousFrom = new Date(currentFrom.getTime() - comparisonDays * 86_400_000);
  const previousTo = new Date(currentFrom.getTime() - 1);
  const date = (value: Date) => value.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
  const comparisonTooltip = `Compared with ${date(previousFrom)}–${date(previousTo)}`;
  const items = [
    ["Total Conversations", summary.metrics.total_conversations, MessagesSquare, "var(--success)", undefined],
    ["Total Messages", summary.metrics.total_messages, MessageCircleMore, "var(--accent-glow)", undefined],
    ["Customer Messages", summary.metrics.customer_messages, MessageSquareText, "var(--teal)", undefined],
    ["Business Replies", summary.metrics.agent_messages, Reply, "var(--warning)", undefined],
    ["Total Customers", summary.metrics.total_customers, Users, "#F59E0B", undefined],
    ["Open Conversations", summary.metrics.open_conversations, CircleAlert, "var(--error)", undefined],
    ["Pending AI Reply Suggestions", summary.metrics.retained_ai_drafts, Sparkles, "var(--teal)", "AI suggestions currently saved and waiting for review. This is not the total number of AI suggestions ever generated."],
    ["Team Members", summary.metrics.team_members, UserRoundCheck, "var(--accent-glow)", undefined],
  ] as const;
  return <section aria-label="Summary KPIs" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
    {items.map(([label, metric, icon, color, tooltip]) => <KpiCard key={label} label={label} metric={metric} icon={icon} color={color} tooltip={tooltip} comparisonLabel="vs previous period" comparisonTooltip={comparisonTooltip} />)}
  </section>;
}
