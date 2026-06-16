"use client";

import { Check, Edit3, X, BookOpen, Bot } from "lucide-react";
import { motion } from "framer-motion";

interface AISuggestionBoxProps {
    suggestion: string;
    sources: string[];
    confidence: number;
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
}: AISuggestionBoxProps) {
    const confidencePct = Math.round(confidence * 100);

    return (
        <motion.div
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.98 }}
            className="mx-4 lg:mx-6 mb-4 bg-gradient-to-r from-[#6D4AE2]/10 to-[#818CF8]/5 border border-[#6D4AE2]/20 rounded-[2rem] p-6 relative overflow-hidden group shadow-md shadow-purple-950/10 font-jakarta"
        >
            {/* Background Bot Accent */}
            <div className="absolute -top-6 -right-6 opacity-[0.04] group-hover:opacity-[0.08] transition-opacity pointer-events-none">
                <Bot size={150} strokeWidth={1} className="text-[#818CF8]" />
            </div>

            {/* Header Area */}
            <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-gradient-to-tr from-[#6D4AE2] to-[#818CF8] rounded-xl flex items-center justify-center text-slate-900 dark:text-white shadow-md shadow-[#6D4AE2]/20">
                    <Bot size={16} className="animate-pulse" />
                </div>
                <div>
                    <span className="font-black text-slate-900 dark:text-white text-[11px] uppercase tracking-[0.2em] block leading-none">AI Assistant</span>
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1 block">Smart Reply</span>
                </div>
                
                <div className="ml-auto flex items-center gap-3">
                    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 border border-surface-border rounded-lg shadow-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[9px] font-black text-[#818CF8] uppercase tracking-widest">
                            {confidencePct}% Match
                        </span>
                    </div>
                    <button
                        onClick={onDismiss}
                        className="p-1 text-slate-400 hover:text-red-400 hover:bg-white/5 rounded-lg transition-all"
                        title="Dismiss Suggestion"
                    >
                        <X size={16} strokeWidth={2.5} />
                    </button>
                </div>
            </div>

            {/* Suggestion Text */}
            <p className="text-[13px] font-medium text-slate-200 mb-4 italic leading-relaxed border-l-3 border-[#818CF8]/40 pl-4 py-1.5">
                "{suggestion}"
            </p>

            {/* Footer Area */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-surface-border">
                {/* Sources list */}
                <div className="flex flex-wrap gap-2">
                    {sources && sources.length > 0 ? (
                        sources.map((source, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 rounded-lg border border-surface-border text-[9px] font-black text-slate-300 uppercase tracking-wider shadow-sm"
                            >
                                <BookOpen size={10} strokeWidth={2.5} className="text-[#818CF8]" />
                                {source}
                            </div>
                        ))
                    ) : (
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                            Knowledge Grounded
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end sm:self-auto">
                    <button
                        onClick={onEdit}
                        className="flex items-center gap-1.5 bg-white/5 border border-surface-border text-slate-300 text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl hover:bg-white/10 hover:border-[#818CF8]/30 hover:text-slate-900 dark:text-white transition-all active:scale-95 shadow-sm"
                    >
                        <Edit3 size={12} strokeWidth={2.5} />
                        Edit
                    </button>
                    <button
                        onClick={onAccept}
                        className="flex items-center gap-1.5 bg-[#6D4AE2] text-white text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl hover:bg-[#5B3BC7] hover-glow transition-all active:scale-95 shadow-xl shadow-purple-950/20"
                    >
                        <Check size={12} strokeWidth={2.5} />
                        Accept
                    </button>
                </div>
            </div>
        </motion.div>
    );
}



