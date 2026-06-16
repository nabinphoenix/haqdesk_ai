"use client";

import { useState, useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import AISuggestionBox from "./AISuggestionBox";
import { motion, AnimatePresence } from "framer-motion";
import {
    Send,
    Smile,
    Paperclip,
    MoreVertical,
    ChevronLeft,
    PanelRightOpen,
    PanelRightClose,
    X,
    CheckCheck,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Message {
    id: number;
    content: string;
    sender: "customer" | "agent" | "ai";
    sender_name?: string | null;
    timestamp: string;
    ai_draft?: string | null;
    ai_language?: string | null;
    sentiment?: string | null;
}

interface ChatWindowProps {
    conversationId: number | null;
    customerName?: string;
    platform?: string;
    customerId?: string;
    onBack?: () => void;
    showCustomerPanel?: boolean;
    onToggleCustomerPanel?: () => void;
}

// ── Platform colors ────────────────────────────────────────────────────────────
const PLATFORM_CONFIG: Record<string, { color: string; label: string }> = {
    whatsapp:  { color: "#25D366", label: "WhatsApp"  },
    facebook:  { color: "#1877F2", label: "Facebook"  },
    instagram: { color: "#E1306C", label: "Instagram" },
    email:     { color: "#06B6D4", label: "Email"     },
};

// ── Platform icon SVG ─────────────────────────────────────────────────────────
function PlatformIcon({ platform, size = 13 }: { platform: string; size?: number }) {
    const p = platform?.toLowerCase();
    if (p === "whatsapp") return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
    );
    if (p === "facebook") return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
    );
    if (p === "instagram") return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
        </svg>
    );
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
        </svg>
    );
}

// ── Emoji picker ───────────────────────────────────────────────────────────────
const EMOJIS = ["🙏","😊","🤝","✨","✅","❤️","👋","💡","🚀","📍","📞","📧","😅","🔥","💬","👍","🎉","⚡"];

// ══════════════════════════════════════════════════════════════════════════════
export default function ChatWindow({
    conversationId,
    customerName,
    platform,
    customerId,
    onBack,
    showCustomerPanel,
    onToggleCustomerPanel,
}: ChatWindowProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [sending, setSending] = useState(false);

    const scrollRef   = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const emojiRef    = useRef<HTMLDivElement>(null);

    // AI suggestion state
    const [aiSuggestion, setAiSuggestion] = useState<Message | null>(null);
    const [aiDismissed, setAiDismissed] = useState(false);
    const prevSuggestionId = useRef<number | null>(null);

    const pColor = PLATFORM_CONFIG[platform?.toLowerCase() || ""]?.color || "#6D4AE2";
    const pLabel = PLATFORM_CONFIG[platform?.toLowerCase() || ""]?.label || platform || "Chat";

    const fetchMessages = async () => {
        if (!conversationId) return;
        const token = localStorage.getItem("token");
        try {
            const res = await fetch(`${API_URL}/api/v1/inbox/conversations/${conversationId}/messages?token=${token}`);
            if (!res.ok) return;
            const data = await res.json();
            const formatted: Message[] = data.map((m: any) => ({
                id: m.id,
                content: m.content,
                sender: m.sender_type,
                sender_name: m.sender_name || null,
                timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                ai_draft: m.ai_draft || null,
                ai_language: m.ai_language || null,
                sentiment: m.sentiment || null,
            }));
            setMessages(prev => {
                if (prev.length === formatted.length) {
                    const last = formatted.length - 1;
                    if (last < 0) return prev;
                    if (prev[last]?.id === formatted[last].id && prev[last]?.content === formatted[last].content) return prev;
                }
                return formatted;
            });
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        if (!conversationId) return;
        fetchMessages();
        const iv = setInterval(fetchMessages, 3000);
        return () => clearInterval(iv);
    }, [conversationId]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    // AI suggestion logic
    useEffect(() => {
        const aiMsgs = messages.filter(m => m.sender === "ai");
        if (aiMsgs.length === 0) { setAiSuggestion(null); return; }
        const lastAi = aiMsgs[aiMsgs.length - 1];
        const lastAiIdx = messages.findIndex(m => m.id === lastAi.id);
        const agentAfter = messages.slice(lastAiIdx + 1).some(m => m.sender === "agent");
        if (!agentAfter) {
            setAiSuggestion(lastAi);
            if (prevSuggestionId.current !== lastAi.id) {
                setAiDismissed(false);
                prevSuggestionId.current = lastAi.id;
            }
        } else {
            setAiSuggestion(null);
        }
    }, [messages]);

    // Reset on conversation change
    useEffect(() => {
        setAiDismissed(false);
        setAiSuggestion(null);
        prevSuggestionId.current = null;
        setInput("");
        setMessages([]);
    }, [conversationId]);

    // Close emoji on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (emojiRef.current && !emojiRef.current.contains(e.target as Node)) {
                setShowEmojiPicker(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    // ── Send message ───────────────────────────────────────────────────────
    const handleSend = async () => {
        if (!input.trim() || !conversationId || sending) return;
        const token = localStorage.getItem("token");
        if (!token) { alert("Session expired. Please login."); return; }

        const text = input.trim();
        setInput("");
        setSending(true);

        // Optimistic
        const currentUserName = localStorage.getItem("userName") || "Agent";
        setMessages(prev => [...prev, {
            id: Date.now(),
            content: text,
            sender: "agent",
            sender_name: currentUserName,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        }]);

        try {
            let res: Response;
            if (platform?.toLowerCase() === "whatsapp" && customerId) {
                res = await fetch(`${API_URL}/api/v1/whatsapp/send`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ to: customerId, message: text }),
                });
            } else {
                res = await fetch(`${API_URL}/api/v1/inbox/conversations/${conversationId}/reply?token=${token}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: text, token }),
                });
            }
            if (res.ok) fetchMessages();
            else console.error("Send failed:", await res.text().catch(() => res.statusText));
        } catch (e) {
            console.error("Network error sending message:", e);
        } finally {
            setSending(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    if (!conversationId) return null;

    // Avatar initials
    const initials = (customerName || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

    return (
        <div className="flex-1 flex flex-col overflow-hidden bg-[var(--background)]">

            {/* ── Header ─────────────────────────────────────────────────── */}
            <header
                className="shrink-0 h-[60px] flex items-center justify-between px-4 border-b border-[var(--border)]"
                style={{ background: "var(--surface)" }}
            >
                <div className="flex items-center gap-3">
                    {/* Mobile back */}
                    {onBack && (
                        <button
                            onClick={onBack}
                            className="sm:hidden w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:bg-black/5 dark:hover:bg-white/5 transition-all"
                        >
                            <ChevronLeft size={18} />
                        </button>
                    )}

                    {/* Avatar */}
                    <div className="relative w-9 h-9 shrink-0">
                        <div
                            className="w-full h-full rounded-xl flex items-center justify-center text-white text-[12px] font-bold"
                            style={{ background: "#6D4AE2" }}
                        >
                            {initials}
                        </div>
                        <div
                            className="absolute -bottom-1 -right-1 w-4 h-4 rounded-md flex items-center justify-center border-2 border-[var(--surface)]"
                            style={{ background: pColor, color: "#fff" }}
                        >
                            <PlatformIcon platform={platform || ""} size={8} />
                        </div>
                    </div>

                    {/* Name + platform */}
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-[14px] font-semibold text-[var(--text-primary)] leading-none">
                                {customerName || "Customer"}
                            </h2>
                            <span
                                className="px-2 py-0.5 rounded-full text-white text-[9px] font-bold flex items-center gap-1"
                                style={{ background: pColor }}
                            >
                                <PlatformIcon platform={platform || ""} size={8} />
                                {pLabel}
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                            <span className="text-[10px] text-[var(--text-secondary)]">Active now</span>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                    {onToggleCustomerPanel && (
                        <button
                            onClick={onToggleCustomerPanel}
                            title={showCustomerPanel ? "Hide customer info" : "Show customer info"}
                            className="hidden lg:flex w-8 h-8 rounded-lg items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5 transition-all"
                        >
                            {showCustomerPanel ? <PanelRightClose size={15} /> : <PanelRightOpen size={15} />}
                        </button>
                    )}
                    <button className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5 transition-all">
                        <MoreVertical size={15} />
                    </button>
                </div>
            </header>

            {/* ── Message stream ──────────────────────────────────────────── */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto custom-scrollbar px-5 py-5 space-y-3"
                style={{ background: "var(--background)" }}
            >
                {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-[12px] text-[var(--text-secondary)]">No messages yet. Say hi! 👋</p>
                    </div>
                ) : (
                    messages.map(msg => {
                        const agentInitials = msg.sender === "agent" && msg.sender_name
                            ? msg.sender_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2)
                            : msg.sender === "ai"
                            ? "AI"
                            : localStorage.getItem("userName")?.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2) || "AG";
                        return (
                            <MessageBubble
                                key={msg.id}
                                {...msg}
                                agentInitials={agentInitials}
                                onUseDraft={(draft) => {
                                    setInput(draft);
                                    setTimeout(() => textareaRef.current?.focus(), 50);
                                }}
                            />
                        );
                    })
                )}
            </div>

            {/* ── AI Suggestion ───────────────────────────────────────────── */}
            <AnimatePresence>
                {aiSuggestion && !aiDismissed && (
                    <AISuggestionBox
                        suggestion={aiSuggestion.content}
                        sources={["Knowledge Base"]}
                        confidence={0.92}
                        onAccept={() => { setInput(aiSuggestion.content); setAiDismissed(true); }}
                        onEdit={() => {
                            setInput(aiSuggestion.content);
                            setAiDismissed(true);
                            setTimeout(() => textareaRef.current?.focus(), 50);
                        }}
                        onDismiss={() => setAiDismissed(true)}
                    />
                )}
            </AnimatePresence>

            {/* ── Compose area ────────────────────────────────────────────── */}
            <div
                className="shrink-0 p-4 border-t border-[var(--border)]"
                style={{ background: "var(--surface)" }}
            >
                {/* Emoji picker */}
                <AnimatePresence>
                    {showEmojiPicker && (
                        <motion.div
                            ref={emojiRef}
                            initial={{ opacity: 0, y: 8, scale: 0.96 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 8, scale: 0.96 }}
                            className="mb-3 p-3 rounded-2xl border border-[var(--border)] shadow-xl"
                            style={{ background: "var(--surface)" }}
                        >
                            <div className="flex items-center justify-between mb-2.5">
                                <span className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Quick Emojis</span>
                                <button onClick={() => setShowEmojiPicker(false)} className="text-[var(--text-secondary)] hover:text-red-400 transition-colors">
                                    <X size={12} />
                                </button>
                            </div>
                            <div className="grid grid-cols-9 gap-1">
                                {EMOJIS.map(e => (
                                    <button
                                        key={e}
                                        onClick={() => setInput(p => p + e)}
                                        className="w-8 h-8 rounded-lg flex items-center justify-center text-[17px] hover:bg-black/5 dark:hover:bg-white/5 transition-all active:scale-90"
                                    >
                                        {e}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="flex flex-col gap-2.5">
                    {/* Textarea */}
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        rows={3}
                        placeholder={`Message ${customerName || "customer"}…`}
                        className="w-full px-4 py-3 rounded-xl text-[13px] outline-none resize-none leading-relaxed transition-all custom-scrollbar"
                        style={{
                            background: "var(--surface-wash)",
                            border: "1px solid var(--border)",
                            color: "var(--text-primary)",
                            minHeight: 80,
                        }}
                    />

                    {/* Toolbar */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setShowEmojiPicker(v => !v)}
                                className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${showEmojiPicker ? "bg-[#6D4AE2] text-white" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5"}`}
                            >
                                <Smile size={15} />
                            </button>
                            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/5 dark:hover:bg-white/5 transition-all">
                                <Paperclip size={15} />
                            </button>
                            <span className="text-[10px] text-[var(--text-secondary)] ml-1 hidden sm:inline">
                                Enter to send · Shift+Enter for newline
                            </span>
                        </div>

                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || sending}
                            className="flex items-center gap-2 px-5 py-2 rounded-xl text-white text-[12px] font-semibold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                            style={{ background: pColor, boxShadow: `0 4px 15px ${pColor}40` }}
                        >
                            {sending ? (
                                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Send size={13} strokeWidth={2.5} />
                            )}
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
