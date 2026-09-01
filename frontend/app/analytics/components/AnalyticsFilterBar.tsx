"use client";

import { CalendarDays, ChevronDown, RotateCcw, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import type { AnalyticsFilterState } from "../types";

function dateValue(value: string) { return value.slice(0, 10); }

function rangeFor(days: number) {
  const to = new Date();
  const from = new Date(to);
  from.setUTCDate(from.getUTCDate() - days);
  return { from: from.toISOString(), to: to.toISOString() };
}

function selectedDays(filters: AnalyticsFilterState) {
  const span = new Date(filters.to).getTime() - new Date(filters.from).getTime();
  return Math.round(span / 86_400_000);
}

export default function AnalyticsFilterBar({ filters, setFilter, setFilters, onReset, agentOptions = [] }: {
  filters: AnalyticsFilterState;
  setFilter: <K extends keyof AnalyticsFilterState>(key: K, value: AnalyticsFilterState[K]) => void;
  setFilters?: (next: Partial<AnalyticsFilterState>) => void;
  onReset: () => void;
  agentOptions?: { id: number; name: string; email: string }[];
}) {
  const [showMore, setShowMore] = useState(false);
  const span = selectedDays(filters);
  const activeRange = useMemo(() => [7, 30, 90].find((days) => Math.abs(span - days) <= 1), [span]);
  const comparisonDays = Math.max(1, span);
  const previousFrom = new Date(new Date(filters.from).getTime() - comparisonDays * 86_400_000);
  const previousTo = new Date(new Date(filters.from).getTime() - 1);
  const shortDate = (value: Date) => value.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  const applyRange = (days: number) => {
    const range = rangeFor(days);
    if (setFilters) setFilters(range);
    else {
      setFilter("from", range.from);
      setFilter("to", range.to);
    }
  };

  return <section aria-label="Analytics filters" className="rounded-2xl border border-surface-border bg-surface p-3 shadow-sm">
    <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <div aria-label="Date range" className="flex rounded-xl border border-surface-border bg-surface-wash p-1">
          {[7, 30, 90].map((days) => <button key={days} type="button" onClick={() => applyRange(days)} className={`rounded-lg px-3 py-2 text-[11px] font-black uppercase tracking-wider transition ${activeRange === days ? "bg-accent text-on-accent shadow-sm" : "text-muted-foreground hover:bg-surface hover:text-foreground"}`}>{days}D</button>)}
        </div>
        <Select label="Channel" value={filters.platform} onChange={(value) => setFilter("platform", value)} options={[["", "All channels"], ["facebook", "Facebook Messenger"], ["instagram", "Instagram"], ["email", "Email"]]} />
        <Select label="Agent" value={filters.agent_id} onChange={(value) => setFilter("agent_id", value)} options={[["", "All agents"], ...agentOptions.map((agent) => [String(agent.id), agent.name || agent.email])]} />
      </div>
      <div className="flex items-center gap-2">
        <button type="button" aria-expanded={showMore} onClick={() => setShowMore((value) => !value)} className="ds-button ds-button-secondary h-10 px-3 text-xs"><SlidersHorizontal size={14} />More filters<ChevronDown size={14} className={showMore ? "rotate-180 transition-transform" : "transition-transform"} /></button>
        <button type="button" onClick={onReset} className="hidden h-10 items-center gap-1.5 rounded-xl px-3 text-xs font-bold text-muted-foreground transition hover:bg-surface-wash hover:text-foreground sm:inline-flex"><RotateCcw size={13} />Reset</button>
      </div>
    </div>
    {showMore && <div className="mt-3 grid gap-3 border-t border-surface-border pt-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">From
        <input aria-label="From date" type="date" value={dateValue(filters.from)} onChange={(event) => setFilter("from", `${event.target.value}T00:00:00.000Z`)} className="ds-input mt-1" />
      </label>
      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">To
        <input aria-label="To date" type="date" value={dateValue(filters.to)} onChange={(event) => setFilter("to", `${event.target.value}T23:59:59.999Z`)} className="ds-input mt-1" />
      </label>
      <Select label="Status" value={filters.status} onChange={(value) => setFilter("status", value)} options={[["", "All statuses"], ["open", "Open"], ["pending", "Pending"], ["resolved", "Resolved"], ["closed", "Closed"]]} />
      <Select label="Priority" value={filters.priority} onChange={(value) => setFilter("priority", value)} options={[["", "All priorities"], ["low", "Low"], ["medium", "Medium"], ["high", "High"], ["urgent", "Urgent"]]} />
      <Select label="Timezone" value={filters.timezone} onChange={(value) => setFilter("timezone", value)} options={[["Asia/Kathmandu", "Kathmandu"], ["UTC", "UTC"]]} />
      <Select label="Comparison" value={filters.comparison} onChange={(value) => setFilter("comparison", value as AnalyticsFilterState["comparison"])} options={[["previous_period", `Previous ${comparisonDays} days (${shortDate(previousFrom)}-${shortDate(previousTo)})`], ["none", "No comparison"]]} />
      <label className="flex h-10 items-center gap-2 self-end text-xs font-medium text-muted-foreground"><input type="checkbox" checked={filters.include_deleted} onChange={(event) => setFilter("include_deleted", event.target.checked)} />Include deleted conversations</label>
      <button type="button" onClick={onReset} className="ds-button ds-button-secondary h-10 self-end sm:hidden"><CalendarDays size={14} />Reset filters</button>
    </div>}
  </section>;
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[][] }) {
  return <label className="min-w-[142px] text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{label}
    <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} className="ds-input mt-1 h-10 py-1.5 text-xs">
      {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
    </select>
  </label>;
}