import Link from "next/link";
import { BookOpen, FilePlus2, RefreshCw, X } from "lucide-react";
import type { FAQOpportunitiesResponse, FAQOpportunity } from "../types";

type FAQOpportunitiesProps = {
  data: FAQOpportunitiesResponse | null;
  loading: boolean;
  error: string;
  actionFingerprint: string | null;
  onRetry: () => void;
  onCreateDraft: (opportunity: FAQOpportunity) => void;
  onDismiss: (opportunity: FAQOpportunity) => void;
};

export default function FAQOpportunities({ data, loading, error, actionFingerprint, onRetry, onCreateDraft, onDismiss }: FAQOpportunitiesProps) {
  const opportunities = data?.opportunities || [];
  return <section className="rounded-[2rem] border border-surface-border bg-surface p-5 sm:p-7">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-[10px] font-black uppercase tracking-[0.22em] text-accent-glow">Knowledge opportunities</p>
        <h2 className="mt-2 font-heading text-2xl font-black tracking-tight">Recurring customer questions</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Turn repeated customer questions into a reviewed FAQ draft. Nothing is published or used for AI replies until an administrator edits and saves it.</p>
      </div>
      {data && <div className="rounded-xl border border-surface-border bg-surface-wash px-3 py-2 text-[10px] font-bold text-muted-foreground">
        {data.analysis_method === "semantic_embeddings" ? "Semantic grouping" : "Text similarity fallback"}
        <span className="mx-1.5">/</span>{data.question_candidates} question candidates
      </div>}
    </div>

    {loading ? <LoadingCards /> : error ? <div role="alert" className="mt-6 flex flex-col gap-3 rounded-2xl border border-[var(--error-border)] bg-[var(--error-surface)] p-5 text-sm text-[var(--error-foreground)] sm:flex-row sm:items-center sm:justify-between"><span>{error}</span><button type="button" onClick={onRetry} className="ds-button ds-button-secondary">Try again</button></div> : opportunities.length === 0 ? <EmptyState minimum={data?.minimum_occurrences || 5} uniqueCustomers={data?.minimum_unique_customers || 3} /> : <div className="mt-6 grid gap-4 lg:grid-cols-2">{opportunities.map((opportunity) => <OpportunityCard key={opportunity.fingerprint} opportunity={opportunity} pending={actionFingerprint === opportunity.fingerprint} onCreateDraft={onCreateDraft} onDismiss={onDismiss} />)}</div>}

    {data && <p className="mt-5 text-[11px] leading-5 text-muted-foreground">{data.privacy_note}</p>}
  </section>;
}

function OpportunityCard({ opportunity, pending, onCreateDraft, onDismiss }: { opportunity: FAQOpportunity; pending: boolean; onCreateDraft: (opportunity: FAQOpportunity) => void; onDismiss: (opportunity: FAQOpportunity) => void }) {
  const channels = Object.entries(opportunity.channels).map(([channel, count]) => `${channel} ${count}`).join(" / ");
  const lastAsked = opportunity.last_asked_at ? new Date(opportunity.last_asked_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "Unknown";
  const hasDraft = opportunity.status === "draft_created" && Boolean(opportunity.knowledge_document_id);
  const title = opportunity.suggested_title.replace(/^FAQ:\s*/i, "");
  return <article className="rounded-2xl border border-surface-border bg-surface-wash p-5">
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-muted-foreground">Suggested FAQ</p><h3 className="mt-1 line-clamp-2 text-lg font-black tracking-tight text-foreground">{title}</h3></div>
      <div className="shrink-0 rounded-xl bg-accent/10 px-2.5 py-2 text-center text-accent-glow"><p className="text-lg font-black leading-none">{opportunity.occurrence_count}</p><p className="mt-1 text-[8px] font-black uppercase tracking-wider">asked</p></div>
    </div>
    <p className="mt-4 line-clamp-2 text-sm leading-6 text-muted-foreground">&ldquo;{opportunity.representative_question}&rdquo;</p>
    <div className="mt-4 flex flex-wrap gap-2 text-[10px] font-bold text-muted-foreground"><span className="rounded-lg border border-surface-border bg-surface px-2 py-1">{opportunity.unique_customer_count} unique customers</span><span className="rounded-lg border border-surface-border bg-surface px-2 py-1">{channels || "No channel data"}</span><span className="rounded-lg border border-surface-border bg-surface px-2 py-1">Last asked {lastAsked}</span></div>
    <details className="mt-4"><summary className="cursor-pointer text-xs font-bold text-accent-glow">See customer wording</summary><ul className="mt-3 space-y-2 border-l-2 border-accent/20 pl-3 text-xs leading-5 text-muted-foreground">{opportunity.example_questions.map((question) => <li key={question}>&ldquo;{question}&rdquo;</li>)}</ul></details>
    <div className="mt-5 flex flex-wrap gap-2">{hasDraft ? <Link href="/knowledge" className="ds-button ds-button-primary"><BookOpen size={14} />Open Knowledge draft</Link> : <button type="button" disabled={pending} onClick={() => onCreateDraft(opportunity)} className="ds-button ds-button-primary">{pending ? <><RefreshCw size={14} className="animate-spin" />Creating...</> : <><FilePlus2 size={14} />Create Knowledge draft</>}</button>}<button type="button" disabled={pending || hasDraft} onClick={() => onDismiss(opportunity)} aria-label={`Dismiss ${title}`} className="ds-button ds-button-secondary px-3"><X size={14} />Dismiss</button></div>
  </article>;
}

function EmptyState({ minimum, uniqueCustomers }: { minimum: number; uniqueCustomers: number }) { return <div className="mt-6 flex min-h-44 flex-col items-center justify-center rounded-2xl border border-dashed border-surface-border bg-surface-wash px-5 text-center"><BookOpen size={27} className="mb-3 text-accent-glow" /><p className="text-sm font-bold text-foreground">No FAQ opportunities yet</p><p className="mt-1 max-w-md text-xs leading-5 text-muted-foreground">An opportunity appears after at least {minimum} similar customer questions from {uniqueCustomers} customers in the selected period. Try a wider date range when support volume is lower.</p></div>; }
function LoadingCards() { return <div className="mt-6 grid gap-3 md:grid-cols-2">{Array.from({ length: 2 }, (_, index) => <div key={index} className="h-52 animate-pulse rounded-2xl border border-surface-border bg-surface-wash" />)}</div>; }