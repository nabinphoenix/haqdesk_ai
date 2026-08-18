"use client";

import { CheckCheck, User, Bot, Paperclip, Download } from "lucide-react";
import { motion } from "framer-motion";

interface MessageBubbleProps {
    content: string;
    sender: "customer" | "agent" | "ai";
    message_type?: string;
    timestamp: string;
    agentInitials?: string;
    ai_draft?: string | null;
    ai_language?: string | null;
    sentiment?: string | null;
    ai_metadata?: any;
    onUseDraft?: (draft: string) => void;
    isVoice?: boolean;
    audioUrl?: string;
}

export default function MessageBubble({
    content,
    sender,
    message_type = "text",
    timestamp,
    agentInitials = "NB",
    ai_draft,
    ai_language,
    sentiment,
    ai_metadata,
    onUseDraft,
    isVoice,
    audioUrl,
}: MessageBubbleProps) {
    // AI messages are shown only via AISuggestionBox — suppress here
    if (sender === "ai") return null;

    const isCustomer = sender === "customer";

    const getFileUrl = (url: string) => {
        if (!url) return "";
        if (url.startsWith("http://") || url.startsWith("https://")) {
            return url;
        }
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const path = url.startsWith("/") ? url.slice(1) : url;
        return `${baseUrl}/${path}`;
    };

    const isMediaUrl = content.startsWith("http") || content.startsWith("/uploads") || content.startsWith("uploads/");
    const resolvedUrl = isMediaUrl ? getFileUrl(content) : "";
    const filename = ai_metadata?.filename || (isMediaUrl ? content.split("/").pop() : "document");

    const isVoiceMsg = isVoice || message_type === "voice" || content === "🎤 Voice message";
    const voiceAudioUrl = audioUrl || ai_metadata?.audio_url || (isMediaUrl ? resolvedUrl : "");

    // Sentiment config
    const sentimentConfig: Record<string, { emoji: string; label: string; border: string; glow: string; text: string }> = {
        positive: { 
            emoji: "😊", 
            label: "Positive", 
            border: "1px solid rgba(16,185,129,0.35)", 
            glow: "0 4px 20px rgba(16,185,129,0.12), 0 0 1px rgba(16,185,129,0.35)", 
            text: "text-[var(--success-foreground)]"
        },
        negative: { 
            emoji: "😠", 
            label: "Negative", 
            border: "1px solid rgba(239,68,68,0.35)", 
            glow: "0 4px 20px rgba(239,68,68,0.12), 0 0 1px rgba(239,68,68,0.35)", 
            text: "text-[var(--error-foreground)]"
        },
        neutral: { 
            emoji: "😐", 
            label: "Neutral", 
            border: "1px solid var(--border)", 
            glow: "0 1px 4px rgba(0,0,0,0.06)", 
            text: "text-muted-foreground"
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
                        <div className={`flex items-center gap-1 text-[10px] font-black ${sentConfig.text} uppercase tracking-wider mb-1 bg-surface-wash px-2 py-0.5 rounded w-max`}>
                            <span>{sentConfig.emoji}</span>
                            <span>{sentConfig.label}</span>
                        </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap">
                        {isVoiceMsg && voiceAudioUrl ? (
                            <div className="flex items-center gap-2 min-w-[180px]">
                                <audio
                                    controls
                                    src={voiceAudioUrl}
                                    className="h-8 w-full"
                                    style={{ filter: "invert(1) hue-rotate(180deg)" }}
                                    preload="metadata"
                                />
                            </div>
                        ) : message_type === "image" && isMediaUrl ? (
                            <a href={resolvedUrl} target="_blank" rel="noopener noreferrer">
                                <img
                                    src={resolvedUrl}
                                    alt="Shared image"
                                    className="max-w-full rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                    style={{ maxHeight: 280, objectFit: "cover" }}
                                    onError={(e) => {
                                        (e.target as HTMLImageElement).style.display = "none";
                                        (e.target as HTMLImageElement).insertAdjacentHTML(
                                            "afterend",
                                            `<span style="opacity:0.6">🖼️ Image could not be loaded</span>`
                                        );
                                    }}
                                />
                            </a>
                        ) : message_type === "video" && isMediaUrl ? (
                            <video
                                controls
                                className="max-w-full rounded-lg"
                                style={{ maxHeight: 280 }}
                                preload="metadata"
                            >
                                <source src={resolvedUrl} />
                                Your browser does not support the video tag.
                            </video>
                        ) : message_type === "audio" && isMediaUrl ? (
                            <audio controls className="w-full min-w-[200px]" preload="metadata">
                                <source src={resolvedUrl} />
                                Your browser does not support the audio tag.
                            </audio>
                        ) : message_type === "file" ? (
                            <div className="flex items-center gap-2.5 py-1">
                                <div
                                    className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                                    style={{
                                        background: isCustomer
                                            ? "var(--surface-wash)"
                                            : "rgba(255,255,255,0.15)",
                                    }}
                                >
                                    <Paperclip size={14} />
                                </div>
                                <span className="text-[13px] font-medium break-all">{filename}</span>
                                {isMediaUrl && (
                                    <a
                                        href={resolvedUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="ml-auto opacity-60 hover:opacity-100 transition-opacity"
                                        download={filename}
                                    >
                                        <Download size={14} />
                                    </a>
                                )}
                            </div>
                        ) : (
                            content
                        )}
                    </div>

                    {/* Inline Suggested Draft Reply */}
                    {isCustomer && ai_draft && (
                        <div className="mt-3.5 pt-3 border-t border-dashed border-border text-left">
                            <div className="flex items-center gap-1.5 mb-2">
                                <div className="w-4.5 h-4.5 bg-gradient-to-tr from-accent to-accent-glow rounded-md flex items-center justify-center text-on-accent shrink-0">
                                    <Bot size={10} className="animate-pulse" />
                                </div>
                                <span className="text-[10px] font-black text-accent-glow uppercase tracking-[0.1em]">AI Draft</span>
                                {ai_language && (
                                    <span className="text-[8px] px-1.5 py-0.2 bg-surface-wash border border-border rounded text-muted-foreground capitalize font-black tracking-wider">
                                        {ai_language}
                                    </span>
                                )}
                            </div>
                            <p className="text-[12px] italic text-muted-foreground bg-surface-wash border border-border p-2.5 rounded-xl pr-3 leading-relaxed">
                                "{ai_draft}"
                            </p>
                            <div className="flex gap-2 mt-2.5">
                                <button
                                    onClick={() => onUseDraft && onUseDraft(ai_draft)}
                                    className="px-3 py-1.5 bg-accent text-on-accent text-[9.5px] font-black uppercase tracking-wider rounded-lg hover:bg-accent-hover active:scale-95 transition-all shadow-md shadow-purple-950/20"
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
                    className="w-7 h-7 rounded-xl shrink-0 flex items-center justify-center mb-0.5 text-foreground text-[9px] font-bold"
                    style={{ background: "linear-gradient(135deg, #6D4AE2, #8B5CF6)" }}
                >
                    {agentInitials}
                </div>
            )}
        </motion.div>
    );
}
