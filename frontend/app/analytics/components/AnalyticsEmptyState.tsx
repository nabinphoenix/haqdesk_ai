import { BarChart3 } from "lucide-react";
export default function AnalyticsEmptyState() { return <div className="flex flex-col items-center gap-3 rounded-3xl border border-surface-border py-20 text-muted-foreground"><BarChart3 size={32} /><p className="text-sm font-bold">No analytics data for these filters</p><p className="text-xs">Try a wider date range or reset the filters.</p></div>; }
