import type { AnalyticsFilterState } from "../types";

function dateValue(value: string) { return value.slice(0, 10); }

export default function AnalyticsFilterBar({ filters, setFilter, onReset, agentOptions = [] }: {
  filters: AnalyticsFilterState;
  setFilter: <K extends keyof AnalyticsFilterState>(key: K, value: AnalyticsFilterState[K]) => void;
  onReset: () => void;
  agentOptions?: { id: number; name: string; email: string }[];
}) {
  const comparisonDays = Math.max(1, Math.round((new Date(filters.to).getTime() - new Date(filters.from).getTime()) / 86_400_000));
  const previousFrom = new Date(new Date(filters.from).getTime() - comparisonDays * 86_400_000);
  const previousTo = new Date(new Date(filters.from).getTime() - 1);
  const shortDate = (value: Date) => value.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  return <section aria-label="Analytics filters" className="mb-6 rounded-2xl border border-surface-border bg-surface-wash p-4">
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-9">
      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">From
        <input aria-label="From date" type="date" value={dateValue(filters.from)} onChange={(event) => setFilter("from", `${event.target.value}T00:00:00.000Z`)} className="ds-input mt-1" />
      </label>
      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">To
        <input aria-label="To date" type="date" value={dateValue(filters.to)} onChange={(event) => setFilter("to", `${event.target.value}T23:59:59.999Z`)} className="ds-input mt-1" />
      </label>
      <Select label="Timezone" value={filters.timezone} onChange={(value) => setFilter("timezone", value)} options={[["Asia/Kathmandu", "Kathmandu"], ["UTC", "UTC"]]} />
      <Select label="Platform" value={filters.platform} onChange={(value) => setFilter("platform", value)} options={[["", "All"], ["facebook", "Facebook"], ["instagram", "Instagram"], ["email", "Email"]]} />
      <Select label="Agent" value={filters.agent_id} onChange={(value) => setFilter("agent_id", value)} options={[["", "All agents"], ...agentOptions.map((agent) => [String(agent.id), agent.name || agent.email])]} />
      <Select label="Status" value={filters.status} onChange={(value) => setFilter("status", value)} options={[["", "All"], ["open", "Open"], ["pending", "Pending"], ["resolved", "Resolved"], ["closed", "Closed"]]} />
      <Select label="Priority" value={filters.priority} onChange={(value) => setFilter("priority", value)} options={[["", "All"], ["low", "Low"], ["medium", "Medium"], ["high", "High"], ["urgent", "Urgent"]]} />
      <Select label="Comparison" value={filters.comparison} onChange={(value) => setFilter("comparison", value as AnalyticsFilterState["comparison"])} options={[["previous_period", `Previous ${comparisonDays} day${comparisonDays === 1 ? "" : "s"} (${shortDate(previousFrom)}–${shortDate(previousTo)})`], ["none", "No comparison"]]} />
      <div className="flex items-end gap-2">
        <label className="flex h-10 items-center gap-2 text-xs text-muted-foreground"><input type="checkbox" checked={filters.include_deleted} onChange={(event) => setFilter("include_deleted", event.target.checked)} /> Deleted</label>
        <button type="button" onClick={onReset} className="ds-button ds-button-secondary h-10">Reset</button>
      </div>
    </div>
  </section>;
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[][] }) {
  return <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{label}
    <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} className="ds-input mt-1">
      {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
    </select>
  </label>;
}
