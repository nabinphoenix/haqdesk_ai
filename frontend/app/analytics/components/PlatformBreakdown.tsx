import { Activity } from "lucide-react";

const COLORS: Record<string, string> = { facebook: "#1877F2", instagram: "#E1306C", whatsapp: "#25D366", email: "#F59E0B" };

export default function PlatformBreakdown({ distribution }: { distribution: Record<string, number> }) {
  const entries = Object.entries(distribution);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  return <section className="rounded-[2.5rem] border border-surface-border bg-surface-wash p-6">
    <div className="mb-6 flex items-center gap-3"><Activity size={16} className="text-accent-glow" /><div><h2 className="text-sm font-black uppercase tracking-widest">By Platform</h2><p className="text-[10px] text-muted-foreground">Conversation distribution</p></div></div>
    <div className="space-y-5">{entries.map(([platform, count]) => <div key={platform}>
      <div className="mb-1.5 flex justify-between"><span className="text-xs font-bold capitalize">{platform}</span><span className="text-xs font-black text-muted-foreground">{count.toLocaleString()}</span></div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-wash"><div className="h-full rounded-full" style={{ width: `${total ? count / total * 100 : 0}%`, background: COLORS[platform] || "#818CF8" }} /></div>
    </div>)}</div>
  </section>;
}
