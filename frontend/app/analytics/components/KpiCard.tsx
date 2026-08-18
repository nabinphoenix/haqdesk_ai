import type { LucideIcon } from "lucide-react";
import { Info } from "lucide-react";
import { formatMetric, metricDelta } from "../analytics-utils";
import type { MetricValue } from "../types";

export default function KpiCard({ label, metric, icon: Icon, color, tooltip, comparisonLabel, comparisonTooltip }: {
  label: string;
  metric: MetricValue;
  icon: LucideIcon;
  color: string;
  tooltip?: string;
  comparisonLabel?: string;
  comparisonTooltip?: string;
}) {
  const delta = metricDelta(metric, comparisonLabel);
  return <article className="rounded-[2rem] border border-surface-border bg-surface-wash p-5">
    <div className="mb-4 flex items-start justify-between gap-2">
      <div className="rounded-xl border border-surface-border bg-surface-wash p-2.5" style={{ color }}><Icon size={17} /></div>
      {metric.status !== "available" && <span title={metric.reason || undefined} className="rounded-full border border-[var(--warning-border)] bg-[var(--warning-surface)] px-2 py-1 text-[9px] font-bold uppercase text-[var(--warning)]">{metric.status === "partial" ? "Limited Data" : "Not Available Yet"}</span>}
    </div>
    <p className="flex items-center gap-1 text-[9px] font-black uppercase tracking-[0.22em] text-muted-foreground" title={tooltip}>{label}{tooltip && <Info aria-label={tooltip} size={11} className="shrink-0 cursor-help" />}</p>
    <p className="mt-1 font-heading text-3xl font-black tracking-tighter text-foreground">{formatMetric(metric)}</p>
    {delta && <p title={comparisonTooltip} aria-label={comparisonTooltip ? `${delta}. ${comparisonTooltip}` : delta} className="mt-1 text-[10px] font-semibold text-muted-foreground">{delta}</p>}
    {!delta && metric.reason && <p className="mt-1 line-clamp-2 text-[10px] text-muted-foreground">{metric.reason}</p>}
  </article>;
}
