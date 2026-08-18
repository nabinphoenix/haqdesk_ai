const SENTIMENT = { positive: { color: "#10B981", label: "Positive" }, neutral: { color: "#64748B", label: "Neutral" }, negative: { color: "#EF4444", label: "Negative" } };

export default function SentimentChart({ distribution }: { distribution: Record<string, number> }) {
  const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
  return <section className="rounded-[2.5rem] border border-surface-border bg-surface-wash p-6">
    <h2 className="text-sm font-black uppercase tracking-widest">Customer Sentiment</h2><p className="mb-6 text-[10px] text-muted-foreground">Analyzed customer messages</p>
    <div className="flex h-3 overflow-hidden rounded-full bg-surface-wash">{Object.entries(SENTIMENT).map(([key, config]) => <div key={key} style={{ width: `${total ? (distribution[key] || 0) / total * 100 : 0}%`, background: config.color }} />)}</div>
    <div className="mt-5 grid grid-cols-3 gap-3">{Object.entries(SENTIMENT).map(([key, config]) => <div key={key}><p className="text-[9px] font-bold uppercase text-muted-foreground">{config.label}</p><p className="text-xl font-black" style={{ color: config.color }}>{distribution[key] || 0}</p></div>)}</div>
  </section>;
}
