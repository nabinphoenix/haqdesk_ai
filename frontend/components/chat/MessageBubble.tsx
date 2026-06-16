"use client";

import { CheckCheck, User, Bot } from "lucide-react";
import { motion } from "framer-motion";

interface MessageBubbleProps {
    content: string;
    sender: "customer" | "agent" | "ai";
    timestamp: string;
    agentInitials?: string;
    ai_draft?: string | null;
    ai_language?: string | null;
    sentiment?: string | null;
    onUseDraft?: (draft: string) => void;
}

export default function MessageBubble({
    content,
    sender,
    timestamp,
    agentInitials = "NB",
    ai_draft,
    ai_language,
    sentiment,
    onUseDraft,
}: MessageBubbleProps) {
    // AI messages are shown only via AISuggestionBox — suppress here
    if (sender === "ai") return null;

    const isCustomer = sender === "customer";

    // Sentiment config
    const sentimentConfig: Record<string, { emoji: string; label: string; border: string; glow: string; text: string }> = {
        positive: { 
            emoji: "😊", 
            label: "Positive", 
            border: "1px solid rgba(16,185,129,0.35)", 
            glow: "0 4px 20px rgba(16,185,129,0.12), 0 0 1px rgba(16,185,129,0.35)", 
            text: "text-emerald-400" 
        },
        negative: { 
            emoji: "😠", 
            label: "Negative", 
            border: "1px solid rgba(239,68,68,0.35)", 
            glow: "0 4px 20px rgba(239,68,68,0.12), 0 0 1px rgba(239,68,68,0.35)", 
            text: "text-red-400" 
        },
        neutral: { 
            emoji: "😐", 
            label: "Neutral", 
            border: "1px solid var(--border)", 
            glow: "0 1px 4px rgba(0,0,0,0.06)", 
            text: "text-slate-400" 
        }
    };

    const sent = sentiment && sentimentConfig[sentiment.toLowerCase()] ? sentiment.toLowerCase() : null;
    const sentConfig = sent ? sentimentConfig[sent] : null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className={`flex w-full items-end gap-2.5 ${isCustomer ? "justify-start" : "justify-end"}`}
        >
            {/* Customer avatar */}
            {isCustomer && (
                <div
                    className="w-7 h-7 rounded-xl shrink-0 flex items-center justify-center mb-0.5"
                    style={{
                        background: "var(--surface-wash)",
                        border: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                    }}
                >
                    <User size={13} strokeWidth={2} />
                </div>
            )}

            {/* Bubble Container */}
            <div className={`max-w-[72%] group ${isCustomer ? "" : "flex flex-col items-end"}`}>
                <div
                    className="px-4 py-2.5 text-[13.5px] leading-relaxed font-medium break-words"
                    style={{
                        borderRadius: isCustomer
                            ? "0.125rem 1.25rem 1.25rem 1.25rem"
                            : "1.25rem 0.125rem 1.25rem 1.25rem",
                        background: isCustomer
                            ? "var(--surface)"
                            : "linear-gradient(135deg, #6D4AE2, #8B5CF6)",
                        color: isCustomer ? "var(--text-primary)" : "#ffffff",
                        border: isCustomer
                            ? (sentConfig ? sentConfig.border : "1px solid var(--border)")
                            : "none",
                        boxShadow: isCustomer
                            ? (sentConfig ? sentConfig.glow : "0 1px 4px rgba(0,0,0,0.06)")
                            : "0 4px 16px rgba(109,74,226,0.30)",
                    }}
                >
                    {/* Sentiment Label inside bubble */}
                    {isCustomer && sentConfig && (
                        <div className={`flex items-center gap-1 text-[10px] font-black ${sentConfig.text} uppercase tracking-wider mb-1 bg-white/5 px-2 py-0.5 rounded w-max`}>
                            <span>{sentConfig.emoji}</span>
                            <span>{sentConfig.label}</span>
                        </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap">{content}</div>

                    {/* Inline Suggested Draft Reply */}
                    {isCustomer && ai_draft && (
                        <div className="mt-3.5 pt-3 border-t border-dashed border-white/10 text-left">
                            <div className="flex items-center gap-1.5 mb-2">
                                <div className="w-4.5 h-4.5 bg-gradient-to-tr from-[#6D4AE2] to-[#818CF8] rounded-md flex items-center justify-center text-white shrink-0">
                                    <Bot size={10} className="animate-pulse" />
                                </div>
                                <span className="text-[10px] font-black text-[#818CF8] uppercase tracking-[0.1em]">AI Draft</span>
                                {ai_language && (
                                    <span className="text-[8px] px-1.5 py-0.2 bg-white/5 border border-white/10 rounded text-slate-400 capitalize font-black tracking-wider">
                                        {ai_language}
                                    </span>
                                )}
                            </div>
                            <p className="text-[12px] italic text-slate-300 bg-black/10 border border-white/5 p-2.5 rounded-xl pr-3 leading-relaxed">
                                "{ai_draft}"
                            </p>
                            <div className="flex gap-2 mt-2.5">
                                <button
                                    onClick={() => onUseDraft && onUseDraft(ai_draft)}
                                    className="px-3 py-1.5 bg-[#6D4AE2] text-white text-[9.5px] font-black uppercase tracking-wider rounded-lg hover:bg-[#5B3BC7] active:scale-95 transition-all shadow-md shadow-purple-950/20"
                                >
                                    Use Reply
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Timestamp + read receipt */}
                <div className={`flex items-center gap-1.5 mt-1 px-1 ${isCustomer ? "justify-start" : "justify-end"}`}>
                    <span className="text-[10px] text-[var(--text-secondary)] opacity-70">{timestamp}</span>
                    {!isCustomer && (
                        <CheckCheck size={11} className="text-sky-400 opacity-80" />
                    )}
                </div>
            </div>

            {/* Agent avatar */}
            {!isCustomer && (
                <div
                    className="w-7 h-7 rounded-xl shrink-0 flex items-center justify-center mb-0.5 text-white text-[9px] font-bold"
                    style={{ background: "linear-gradient(135deg, #6D4AE2, #8B5CF6)" }}
                >
                    {agentInitials}
                </div>
            )}
        </motion.div>
    );
}
