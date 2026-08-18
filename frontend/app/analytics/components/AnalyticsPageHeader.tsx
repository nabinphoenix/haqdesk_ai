import { Download, RefreshCw } from "lucide-react";

export default function AnalyticsPageHeader({ generatedAt, refreshing, exporting, exportDisabled, exportError, onRefresh, onExport }: {
  generatedAt?: string;
  refreshing: boolean;
  exporting: "csv" | "pdf" | null;
  exportDisabled: boolean;
  exportError?: string;
  onRefresh: () => void;
  onExport: (format: "csv" | "pdf") => void;
}) {
  return <header className="page-header">
    <div className="page-header-row">
      <div>
        <h1 className="font-heading text-4xl font-black tracking-tighter text-foreground sm:text-5xl">Analytics</h1>
        <p className="mt-2 text-sm font-medium text-muted-foreground">Understand conversation activity, channels, customers, and support workload.</p>
        {generatedAt && <p className="mt-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Updated {new Date(generatedAt).toLocaleString()}</p>}
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="flex gap-2">
          <button type="button" onClick={() => onExport("csv")} disabled={Boolean(exporting) || exportDisabled} className="ds-button ds-button-secondary">
            <Download size={14} /> {exporting === "csv" ? "Exporting..." : "Export CSV"}
          </button>
          <button type="button" onClick={() => onExport("pdf")} disabled={Boolean(exporting) || exportDisabled} className="ds-button ds-button-secondary">
            <Download size={14} /> {exporting === "pdf" ? "Exporting..." : "Export PDF"}
          </button>
          <button type="button" onClick={onRefresh} disabled={refreshing} className="ds-button ds-button-secondary">
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        {exportError && <p role="alert" className="text-xs font-semibold text-[var(--error-foreground)]">{exportError}</p>}
      </div>
    </div>
  </header>;
}
