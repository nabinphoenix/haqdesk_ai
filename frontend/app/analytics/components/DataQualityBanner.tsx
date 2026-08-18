import { AlertTriangle, Info } from "lucide-react";
import type { DataQualityNotice } from "../types";

export default function DataQualityBanner({ notices }: { notices: DataQualityNotice[] }) {
  if (!notices.length) return null;
  return <section aria-label="Data quality notices" className="space-y-2">{notices.map((notice) => <div key={`${notice.metric}-${notice.message}`} className={`flex gap-3 rounded-xl border p-3 text-xs ${notice.severity === "warning" ? "border-[var(--warning-border)] bg-[var(--warning-surface)] text-[var(--warning)]" : "border-accent/20 bg-accent/10 text-accent-glow"}`}>
    {notice.severity === "warning" ? <AlertTriangle size={14} className="shrink-0" /> : <Info size={14} className="shrink-0" />}<span>{notice.message.replace(/\bpartial\b/gi, "limited")}</span>
  </div>)}</section>;
}
