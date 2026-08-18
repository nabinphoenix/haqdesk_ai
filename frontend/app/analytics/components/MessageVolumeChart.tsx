import { BarChart3 } from "lucide-react";
import type { MessageTrend } from "../types";

const COLORS = { all_messages: "#818CF8", customer_messages: "#06B6D4", agent_messages: "#F59E0B" };

export default function MessageVolumeChart({ trend }: { trend: MessageTrend }) {
  const max = Math.max(1, ...trend.series.flatMap((series) => series.points.map((point) => point.value)));
  const points = trend.series[0]?.points || [];
  return <section className="rounded-[2.5rem] border border-surface-border bg-surface-wash p-6 lg:col-span-2">
    <div className="mb-6 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3"><BarChart3 size={16} className="text-accent-glow" /><div><h2 className="text-sm font-black uppercase tracking-widest">Message Volume</h2><p className="text-[10px] text-muted-foreground">Zero-filled {trend.bucket} buckets</p></div></div>
      <div className="flex flex-wrap gap-3">{trend.series.map((series) => <span key={series.key} className="flex items-center gap-1.5 text-[9px] font-bold text-muted-foreground"><span className="h-2 w-2 rounded-full" style={{ background: COLORS[series.key] }} />{series.key === "agent_messages" ? "Business replies" : series.label}</span>)}</div>
    </div>
    <div className="flex h-56 items-end gap-1 overflow-x-auto pb-1">
      {points.map((point, index) => <div key={point.start} className="group flex h-full min-w-[14px] flex-1 items-end gap-px" title={new Date(point.start).toLocaleString()}>
        {trend.series.map((series) => <div key={series.key} className="min-h-px flex-1 rounded-t-sm transition-opacity group-hover:opacity-80" style={{ height: `${(series.points[index].value / max) * 100}%`, background: COLORS[series.key] }} title={`${series.key === "agent_messages" ? "Business replies" : series.label}: ${series.points[index].value}`} />)}
      </div>)}
    </div>
    <div className="mt-3 flex justify-between text-[9px] font-bold uppercase tracking-wider text-muted-foreground"><span>{points[0] ? new Date(points[0].start).toLocaleString() : "No data"}</span><span>{points.at(-1) ? new Date(points.at(-1)!.start).toLocaleString() : ""}</span></div>
  </section>;
}
