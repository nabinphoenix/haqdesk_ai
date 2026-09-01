"use client";

import { Check, Edit3, X, BookOpen, Bot } from "lucide-react";
import { motion } from "framer-motion";

interface AISuggestionBoxProps {
    suggestion: string;
    sources: string[];
    confidence: number;
    grounded?: boolean;
    sourceDetails?: Array<{ filename: string; page_number?: number | null; similarity?: number; source_type?: string }>;
    onAccept: () => void;
    onEdit: () => void;
    onDismiss: () => void;
}

export default function AISuggestionBox({
    suggestion,
    sources,
    confidence,
    onAccept,
    onEdit,
    onDismiss,
    grounded = false,
    sourceDetails = [],
}: AISuggestionBoxProps) {
    const confidencePct = Math.round(Math.max(0, Math.min(1, confidence)) * 100);

    return (
        <motion.div
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.98 }}
            className="mx-4 lg:mx-6 mb-4 bg-gradient-to-r from-accent/10 to-accent-glow/5 border border-accent/20 rounded-[2rem] p-6 relative overflow-hidden group shadow-md shadow-purple-950/10 font-jakarta"
        >
            {/* Background Bot Accent */}
            <div className="absolute -top-6 -right-6 opacity-[0.04] group-hover:opacity-[0.08] transition-opacity pointer-events-none">
                <Bot size={150} strokeWidth={1} className="text-accent-glow" />
            </div>

            {/* Header Area */}
            <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-gradient-to-tr from-accent to-accent-glow rounded-xl flex items-center justify-center text-on-accent dark:text-on-accent shadow-md shadow-lg">
                    <Bot size={16} className="animate-pulse" />
                </div>
                <div>
                    <span className="font-black text-foreground dark:text-foreground text-[11px] uppercase tracking-[0.2em] block leading-none">AI Assistant</span>
                    <span className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mt-1 block">Smart Reply</span>
                </div>
                
                <div className="ml-auto flex items-center gap-3">
                    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-wash border border-surface-border rounded-lg shadow-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
                        <span className="text-[9px] font-black text-accent-glow uppercase tracking-widest">
                            {grounded ? `${confidencePct}% grounded` : "Needs review"}
                        </span>
                    </div>
                    <button
                        onClick={onDismiss}
                        className="p-1 text-muted-foreground hover:text-[var(--error-foreground)] hover:bg-surface-wash rounded-lg transition-all"
                        title="Dismiss Suggestion"
                    >
                        <X size={16} strokeWidth={2.5} />
                    </button>
                </div>
            </div>

            {/* Suggestion Text */}
            <p className="text-[13px] font-medium text-foreground mb-4 italic leading-relaxed border-l-3 border-accent-glow/40 pl-4 py-1.5">
                "{suggestion}"
            </p>

            {/* Footer Area */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-surface-border">
                {/* Sources list */}
                <div className="flex flex-wrap gap-2">
                    {grounded && sources && sources.length > 0 ? (
                        sources.map((source, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-wash rounded-lg border border-surface-border text-[9px] font-black text-muted-foreground uppercase tracking-wider shadow-sm"
                            >
                                <BookOpen size={10} strokeWidth={2.5} className="text-accent-glow" />
                                {source}{(() => {
                                    const detail = sourceDetails.find((item) => item.filename === source);
                                    return detail?.page_number ? " - p." + detail.page_number : "";
                                })()}
                            </div>
                        ))
                    ) : (
                        <div className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider">
                            No matching knowledge source - verify before sending
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end sm:self-auto">
                    <button
                        onClick={onEdit}
                        className="flex items-center gap-1.5 bg-surface-wash border border-surface-border text-muted-foreground text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl hover:bg-surface-wash hover:border-accent-glow/30 hover:text-foreground dark:text-foreground transition-all active:scale-95 shadow-sm"
                    >
                        <Edit3 size={12} strokeWidth={2.5} />
                        Edit
                    </button>
                    <button
                        onClick={onAccept}
                        className="flex items-center gap-1.5 bg-accent text-on-accent text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl hover:bg-accent-hover hover-glow transition-all active:scale-95 shadow-xl shadow-purple-950/20"
                    >
                        <Check size={12} strokeWidth={2.5} />
                        Accept
                    </button>
                </div>
            </div>
        </motion.div>
    );
}



