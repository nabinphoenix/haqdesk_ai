"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import ChatWindow from "@/components/chat/ChatWindow";
import CustomerSidebar from "@/components/chat/CustomerSidebar";
import { fetchWithAuth } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import ConfirmModal from "@/components/ui/ConfirmModal";
import {
    Search,
    MessageSquare,
    Users,
    Filter,
    ChevronDown,
    Circle,
    Inbox,
    Zap,
    RefreshCw,
    Trash2,
} from "lucide-react";
import { toast } from "sonner";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Conversation {
    id: number;
    customer_name: string;
    customer_email?: string;
    customer_id: string;
    last_message: string;
    time: string;
    rawTime: string;
    status: string;
    platform: string;
    unread?: number;
    priority?: string;
}

// ── Platform config ────────────────────────────────────────────────────────────
const PLATFORM_CONFIG = {
    all:       { label: "All",       color: "#6D4AE2", bg: "rgba(109,74,226,0.15)" },
    whatsapp:  { label: "WhatsApp",  color: "#25D366", bg: "rgba(37,211,102,0.15)" },
    facebook:  { label: "Facebook",  color: "#1877F2", bg: "rgba(24,119,242,0.15)" },
    instagram: { label: "Instagram", color: "#E1306C", bg: "rgba(225,48,108,0.15)" },
    email:     { label: "Email",     color: "#06B6D4", bg: "rgba(6,182,212,0.15)"  },
} as const;

type PlatformKey = keyof typeof PLATFORM_CONFIG;

// ── SVG platform icons ─────────────────────────────────────────────────────────
function PlatformIcon({ platform, size = 16 }: { platform: string; size?: number }) {
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
    if (p === "email") return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
        </svg>
    );
    // All / default
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
    );
}

// ── Avatar ─────────────────────────────────────────────────────────────────────
function Avatar({ name, size = 40, platform }: { name: string; size?: number; platform?: string }) {
    const initials = (name || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
    const colors = ["#6D4AE2", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];
    const hue = initials.charCodeAt(0) % colors.length;
    const bg = colors[hue];
    const pColor = platform ? PLATFORM_CONFIG[platform.toLowerCase() as PlatformKey]?.color : undefined;

    return (
        <div className="relative shrink-0" style={{ width: size, height: size }}>
            <div
                className="w-full h-full rounded-2xl flex items-center justify-center font-bold text-white"
                style={{ background: bg, fontSize: size * 0.35 }}
            >
                {initials}
            </div>
            {platform && pColor && (
                <div
                    className="absolute -bottom-1 -right-1 rounded-md flex items-center justify-center border-2 border-[var(--background)]"
                    style={{ width: size * 0.46, height: size * 0.46, background: pColor, color: "#fff" }}
                >
                    <PlatformIcon platform={platform} size={size * 0.26} />
                </div>
            )}
        </div>
    );
}

// ── Status dot ─────────────────────────────────────────────────────────────────
function StatusDot({ status }: { status: string }) {
    const color = status === "open" ? "#10B981" : status === "pending" ? "#F59E0B" : "#64748B";
    return <span className="w-2 h-2 rounded-full inline-block" style={{ background: color }} />;
}

// ── Relative time ──────────────────────────────────────────────────────────────
function relativeTime(raw: string) {
    const now = Date.now();
    const then = new Date(raw).getTime();
    const diff = Math.floor((now - then) / 1000);
    if (diff < 60) return "now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ══════════════════════════════════════════════════════════════════════════════
export default function InboxPage() {
    const router = useRouter();
    const [isAuth, setIsAuth] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState<PlatformKey>("all");
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
    const selectedConvIdRef = useRef<number | null>(null);

    useEffect(() => {
        selectedConvIdRef.current = selectedConvId;
    }, [selectedConvId]);
    const [search, setSearch] = useState("");
    const [mobileView, setMobileView] = useState<"list" | "chat">("list");
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [showCustomerPanel, setShowCustomerPanel] = useState(true);
    const [deletedConversations, setDeletedConversations] = useState<any[]>([]);
    const [showDeleted, setShowDeleted] = useState(false);
    const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);
    const [aiMode, setAiMode] = useState<"auto" | "review">("review");
    const [isLoading, setIsLoading] = useState(true);

    const audioRef = useRef<HTMLAudioElement | null>(null);
    const previousMessageCountRef = useRef<Map<number, string>>(new Map());

    useEffect(() => {
        audioRef.current = new Audio("/audio/sound_notification_haqdeskAI.mp3");
        audioRef.current.volume = 0.6;
    }, []);

    const playNotificationSound = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current.play().catch((err) => {
                console.warn("Audio play blocked or failed:", err);
            });
        }
    }, []);

    const fetchAiMode = useCallback(async () => {
        try {
            const res = await fetchWithAuth("/api/v1/settings/business");
            if (res.ok) {
                const data = await res.json();
                if (data.ai_response_mode) {
                    setAiMode(data.ai_response_mode);
                }
            }
        } catch (e) {
            console.error("Failed to fetch AI mode:", e);
        }
    }, []);

    const handleToggleAiMode = async () => {
        const nextMode = aiMode === "auto" ? "review" : "auto";
        setAiMode(nextMode);
        try {
            const res = await fetchWithAuth("/api/v1/settings/business", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ai_response_mode: nextMode }),
            });
            if (res.ok) {
                toast.success(`AI Mode set to ${nextMode === "auto" ? "Auto AI Mode" : "Review Mode"}`);
            } else {
                setAiMode(aiMode);
                toast.error("Failed to update AI mode");
            }
        } catch (e) {
            setAiMode(aiMode);
            toast.error("Network error updating AI mode");
        }
    };

    const fetchConversations = useCallback(async () => {
        try {
            const response = await fetchWithAuth(
                `/api/v1/inbox/conversations?t=${Date.now()}`,
                { cache: "no-store" }
            );
            
            if (response.status === 401) {
                console.warn("Token expired or invalid, redirecting to login");
                localStorage.removeItem("token");
                localStorage.removeItem("user");
                router.push("/login");
                return;
            }

            if (!response.ok) {
                console.error("Fetch conversations failed with status:", response.status);
                return;
            }

            const data = await response.json();
            console.log("Conversations response:", data);
            
            // Detect new incoming customer messages for sound notification
            data.forEach((conv: any) => {
                const key = Number(conv.id);
                const prevTime = previousMessageCountRef.current.get(key);
                const currentTime = conv.time;

                const isFirstLoad = prevTime === undefined;
                const hasNewActivity = !isFirstLoad && prevTime !== currentTime;

                const isFromCustomer = conv.last_message_sender_type === "customer";
                const isCurrentlyOpenConversation = conv.id === selectedConvIdRef.current;

                if (hasNewActivity && isFromCustomer && !isCurrentlyOpenConversation) {
                    // Something changed in this conversation since last poll — play sound and show toast
                    playNotificationSound();
                    
                    // Show a toast notification
                    const previewText = conv.last_message || "New message received";
                    const senderName = conv.customer_name || "Customer";
                    toast.info(`New message from ${senderName}`, {
                        description: previewText.substring(0, 50) + (previewText.length > 50 ? "..." : ""),
                        duration: 5000,
                        action: {
                            label: "View",
                            onClick: () => setSelectedConvId(conv.id)
                        }
                    });
                }
                previousMessageCountRef.current.set(key, currentTime);
            });

            const mappedData = data.map((c: any) => ({
                ...c,
                rawTime: c.time,
                time: relativeTime(c.time),
                unread: c.unread ?? 0,
            }));

            setConversations(prev => {
                const isDifferent = JSON.stringify(prev.map(p => ({ id: p.id, last_message: p.last_message, unread: p.unread, status: p.status, rawTime: p.rawTime }))) !==
                                     JSON.stringify(mappedData.map((d: any) => ({ id: d.id, last_message: d.last_message, unread: d.unread, status: d.status, rawTime: d.rawTime })));
                return isDifferent ? mappedData : prev;
            });
        } catch (e) {
            console.error("Failed to fetch conversations:", e);
        } finally {
            setIsLoading(false);
        }
    }, [router, playNotificationSound]);

    // Auth guard
    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) { router.push("/login"); return; }
        setIsAuth(true);
        fetchConversations();
        fetchAiMode();
        
        const interval = setInterval(fetchConversations, 3000);
        
        // Listen for link events to immediately refresh list
        const handleLinkEvent = () => fetchConversations();
        window.addEventListener('customerLinked', handleLinkEvent);
        
        return () => {
            clearInterval(interval);
            window.removeEventListener('customerLinked', handleLinkEvent);
        };
    }, [router, fetchConversations, fetchAiMode]);

    const handleDeleteConversation = (conversationId: number) => {
        setConfirmDeleteId(conversationId);
    };

    const executeDeleteConversation = async () => {
        if (confirmDeleteId === null) return;
        setIsDeleting(true);
        try {
            const res = await fetchWithAuth(`/api/v1/inbox/conversations/${confirmDeleteId}`, {
                method: "DELETE",
            });
            if (res.ok) {
                setConversations(prev => prev.filter(c => c.id !== confirmDeleteId));
                if (selectedConvId === confirmDeleteId) {
                    setSelectedConvId(null);
                }
                toast.success("Conversation deleted");
                fetchDeletedConversations();
            } else {
                toast.error("Failed to delete conversation");
            }
        } catch (e) {
            toast.error("Network error");
        } finally {
            setIsDeleting(false);
            setConfirmDeleteId(null);
        }
    };

    const fetchDeletedConversations = async () => {
        try {
            const res = await fetchWithAuth("/api/v1/inbox/conversations/deleted");
            if (res.ok) {
                const data = await res.json();
                setDeletedConversations(data);
            }
        } catch (e) { console.error(e); }
    };

    const handleRestoreConversation = async (conversationId: number) => {
        try {
            const res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}/restore`, {
                method: "POST",
            });
            if (res.ok) {
                setDeletedConversations(prev => prev.filter(c => c.id !== conversationId));
                fetchConversations();
                toast.success("Conversation restored");
            }
        } catch (e) { toast.error("Restore failed"); }
    };

    useEffect(() => {
        if (showDeleted) {
            fetchDeletedConversations();
        }
    }, [showDeleted]);

    const handleUpdatePriority = async (conversationId: number, priority: string) => {
        try {
            const res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ priority }),
            });
            if (res.ok) {
                setConversations(prev => prev.map(c =>
                    c.id === conversationId ? { ...c, priority } : c
                ));
                toast.success(`Priority set to ${priority}`);
            }
        } catch (e) {
            console.error("Priority update failed:", e);
        }
    };

    const handleRefresh = async () => {
        setIsRefreshing(true);
        await fetchConversations();
        setTimeout(() => setIsRefreshing(false), 600);
    };

    const filtered = conversations.filter(c => {
        const matchPlatform = selectedPlatform === "all" || c.platform.toLowerCase() === selectedPlatform;
        const matchSearch = !search || c.customer_name.toLowerCase().includes(search.toLowerCase()) || c.last_message?.toLowerCase().includes(search.toLowerCase());
        return matchPlatform && matchSearch;
    });

    const selectedConv = conversations.find(c => c.id === selectedConvId);

    if (!isAuth) return null;

    const platforms: PlatformKey[] = ["all", "whatsapp", "facebook", "instagram", "email"];
    const platformCounts: Record<string, number> = {};
    conversations.forEach(c => {
        const p = c.platform.toLowerCase();
        platformCounts[p] = (platformCounts[p] || 0) + 1;
    });

    return (
        <div className="h-full flex overflow-hidden">
            <ConfirmModal
                isOpen={confirmDeleteId !== null}
                title="Delete Conversation"
                message="This conversation and all its messages will be permanently deleted. This action cannot be undone."
                confirmLabel={isDeleting ? "Deleting…" : "Delete"}
                cancelLabel="Cancel"
                onConfirm={executeDeleteConversation}
                onCancel={() => setConfirmDeleteId(null)}
                isDangerous={true}
            />

            {/* ── COL 1: Platform icon rail ─────────────────────────────────── */}
            <div className="w-[72px] shrink-0 flex flex-col items-center py-4 gap-2 border-r border-[var(--border)] bg-[var(--surface)] z-30">
                <div className="mb-2 w-9 h-9 rounded-xl flex items-center justify-center bg-[#6D4AE2]/10">
                    <Inbox size={16} className="text-[#6D4AE2]" />
                </div>

                <div className="w-full px-2 flex flex-col gap-1.5">
                    {platforms.map(p => {
                        const cfg = PLATFORM_CONFIG[p];
                        const isActive = selectedPlatform === p;
                        const count = p === "all" ? conversations.length : (platformCounts[p] || 0);
                        return (
                            <button
                                key={p}
                                onClick={() => setSelectedPlatform(p)}
                                title={cfg.label}
                                className="relative w-full aspect-square rounded-xl flex flex-col items-center justify-center gap-0.5 transition-all duration-200 group"
                                style={{
                                    background: isActive ? cfg.bg : "transparent",
                                    color: isActive ? cfg.color : "var(--text-secondary)",
                                    border: isActive ? `1.5px solid ${cfg.color}30` : "1.5px solid transparent",
                                }}
                            >
                                <PlatformIcon platform={p} size={18} />
                                {count > 0 && (
                                    <span className="text-[8px] font-bold leading-none" style={{ color: isActive ? cfg.color : "var(--text-secondary)" }}>
                                        {count > 99 ? "99+" : count}
                                    </span>
                                )}
                                {/* Tooltip */}
                                <span className="absolute left-full ml-2.5 px-2 py-1 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-[11px] font-semibold text-[var(--text-primary)] whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity shadow-lg z-50">
                                    {cfg.label}
                                </span>
                            </button>
                        );
                    })}
                </div>

                {/* Spacer */}
                <div className="flex-1" />

                {/* Refresh */}
                <button
                    onClick={handleRefresh}
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--text-secondary)] hover:text-[#6D4AE2] hover:bg-[#6D4AE2]/10 transition-all"
                    title="Refresh"
                >
                    <RefreshCw size={15} className={isRefreshing ? "animate-spin" : ""} />
                </button>
            </div>

            {/* ── COL 2: Conversation list ──────────────────────────────────── */}
            <div
                className={`
                    w-full sm:w-[320px] lg:w-[340px] shrink-0 flex flex-col
                    border-r border-[var(--border)] bg-[var(--surface)] z-20
                    ${mobileView === "chat" ? "hidden sm:flex" : "flex"}
                `}
            >
                {/* Header */}
                <div className="px-4 pt-4 pb-3 border-b border-[var(--border)]">
                    <div className="flex items-center justify-between mb-3">
                        <div>
                            <h1 className="text-[15px] font-bold text-[var(--text-primary)] tracking-tight">
                                {PLATFORM_CONFIG[selectedPlatform].label}
                            </h1>
                            <p className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                                {filtered.length} conversation{filtered.length !== 1 ? "s" : ""}
                            </p>
                        </div>
                        <button
                            onClick={handleToggleAiMode}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[10px] font-black uppercase tracking-wider transition-all shadow-sm ${
                                aiMode === "auto"
                                    ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/25"
                                    : "bg-[#6D4AE2]/15 border-[#6D4AE2]/40 text-[#818CF8] hover:bg-[#6D4AE2]/25"
                            }`}
                            title="Toggle between Autonomous Auto-Send and Manual Review Mode"
                        >
                            <Zap size={12} strokeWidth={2.5} />
                            {aiMode === "auto" ? "🚀 Auto AI Mode" : "👁️ Review Mode"}
                        </button>
                    </div>

                    {/* Search */}
                    <div className="relative">
                        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                        <input
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Search conversations…"
                            className="w-full pl-8 pr-3 py-2 rounded-xl text-[12.5px] outline-none transition-all"
                            style={{
                                background: "var(--surface-wash)",
                                border: "1px solid var(--border)",
                                color: "var(--text-primary)",
                            }}
                        />
                    </div>

                    {/* Toggle between All and Deleted */}
                    <div className="flex items-center gap-2 mt-3 bg-[var(--surface-wash)] p-1 rounded-xl border border-[var(--border)]">
                        <button
                            onClick={() => setShowDeleted(false)}
                            className={`flex-1 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
                                !showDeleted
                                    ? "bg-[#6D4AE2] text-white shadow-sm"
                                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                            }`}
                        >
                            All ({conversations.length})
                        </button>
                        <button
                            onClick={() => setShowDeleted(true)}
                            className={`flex-1 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
                                showDeleted
                                    ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                    : "text-[var(--text-secondary)] hover:text-red-400"
                            }`}
                        >
                            Deleted ({deletedConversations.length})
                        </button>
                    </div>
                </div>

                {/* Conversation list */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {showDeleted ? (
                        <div className="p-2 space-y-0.5">
                            {deletedConversations.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full gap-3 text-[var(--text-secondary)] py-12">
                                    <Trash2 size={28} className="opacity-30" />
                                    <p className="text-[12px] text-center">No deleted conversations</p>
                                </div>
                            ) : (
                                deletedConversations.map(conv => (
                                    <div
                                        key={conv.id}
                                        className="relative group flex items-center gap-3 px-3 py-3 rounded-xl border border-transparent hover:bg-white/5 transition-all"
                                    >
                                        {/* Avatar */}
                                        <Avatar name={conv.customer_name} size={40} platform={conv.platform} />

                                        {/* Info */}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate">{conv.customer_name}</p>
                                            <p className="text-[11.5px] text-[var(--text-secondary)] truncate">{conv.last_message || "No messages yet"}</p>
                                            <p className="text-[10px] text-red-400 mt-0.5">
                                                Deleted {conv.deleted_at ? new Date(conv.deleted_at).toLocaleDateString() : ""}
                                            </p>
                                        </div>

                                        {/* Restore button */}
                                        <button
                                            onClick={() => handleRestoreConversation(conv.id)}
                                            className="opacity-0 group-hover:opacity-100 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30 text-[10px] font-bold hover:bg-purple-500/30 transition-all cursor-pointer"
                                        >
                                            <RefreshCw size={11} />
                                            Restore
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    ) : isLoading ? (
                        <div className="p-3 space-y-2.5">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-[var(--surface-wash)] animate-pulse border border-[var(--border)]">
                                    <div className="w-10 h-10 rounded-2xl bg-[var(--border)] shrink-0 opacity-40" />
                                    <div className="flex-1 space-y-2 min-w-0">
                                        <div className="h-3.5 w-28 bg-[var(--border)] rounded opacity-40" />
                                        <div className="h-2.5 w-40 bg-[var(--border)] rounded opacity-25" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full gap-3 text-[var(--text-secondary)] p-8">
                            <MessageSquare size={28} className="opacity-30" />
                            <p className="text-[12px] text-center">No conversations found</p>
                        </div>
                    ) : (
                        <div className="p-2 space-y-0.5">
                            {filtered.map(conv => {
                                const isActive = selectedConvId === conv.id;
                                const pColor = PLATFORM_CONFIG[conv.platform.toLowerCase() as PlatformKey]?.color || "#6D4AE2";
                                const isUnread = (conv.unread ?? 0) > 0;
                                return (
                                    <div key={conv.id} className="relative group">
                                        <motion.div
                                            layout
                                            initial={false}
                                            onClick={async () => {
                                                setSelectedConvId(conv.id);
                                                setMobileView("chat");
                                                try {
                                                    await fetchWithAuth(`/api/v1/inbox/conversations/${conv.id}/mark-read`, {
                                                        method: "POST",
                                                    });
                                                    setConversations(prev => prev.map(c =>
                                                        c.id === conv.id ? { ...c, unread: 0 } : c
                                                    ));
                                                } catch (e) {
                                                    console.error("Failed to mark conversation as read:", e);
                                                }
                                            }}
                                            whileTap={{ scale: 0.99 }}
                                            className="w-full px-3 py-3 rounded-xl text-left cursor-pointer transition-all duration-150 flex items-start gap-3"
                                            style={{
                                                background: isActive
                                                    ? "rgba(109,74,226,0.10)"
                                                    : "transparent",
                                                border: isActive
                                                    ? "1px solid rgba(109,74,226,0.20)"
                                                    : "1px solid transparent",
                                            }}
                                        >
                                            <Avatar name={conv.customer_name} size={40} platform={conv.platform} />

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between mb-0.5">
                                                    <div className="flex items-center gap-1.5 min-w-0">
                                                        {conv.priority && conv.priority !== "medium" && (
                                                            <span className={`w-2 h-2 rounded-full shrink-0 ${
                                                                conv.priority === "urgent" ? "bg-red-500" :
                                                                conv.priority === "high" ? "bg-orange-400" :
                                                                conv.priority === "low" ? "bg-emerald-500" :
                                                                "bg-yellow-400"
                                                            }`} title={`Priority: ${conv.priority}`} />
                                                        )}
                                                        <span className={`text-[13px] truncate max-w-[140px] ${
                                                            isUnread ? "font-bold text-[var(--text-primary)]" : "font-medium text-[var(--text-secondary)]"
                                                        }`}>
                                                            {conv.customer_name}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-1.5 shrink-0 ml-1">
                                                        <span className="text-[10px] text-[var(--text-secondary)]">{conv.time}</span>
                                                    </div>
                                                </div>
                                                <div className="flex items-center justify-between gap-2">
                                                    <p className={`text-[11.5px] truncate leading-relaxed flex-1 ${
                                                        isUnread ? "font-semibold text-[var(--text-primary)]" : "font-normal text-[var(--text-secondary)]"
                                                    }`}>
                                                        {conv.last_message || "No messages yet"}
                                                    </p>
                                                    <div className="flex items-center gap-1.5 shrink-0">
                                                        <StatusDot status={conv.status} />
                                                        {isUnread && (
                                                            <span
                                                                className="min-w-[18px] h-[18px] px-1 rounded-full text-white text-[9px] font-bold flex items-center justify-center"
                                                                style={{ background: pColor }}
                                                            >
                                                                {conv.unread}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>

                                        {/* Action buttons - show on hover */}
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-1 bg-[#1a1a2e] rounded-lg p-1 border border-white/10 z-10">
                                            {/* Priority selector */}
                                            <select
                                                value={conv.priority || "medium"}
                                                onChange={(e) => handleUpdatePriority(conv.id, e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="text-[10px] font-bold px-2 py-1 rounded-lg bg-transparent text-gray-300 border border-white/10 cursor-pointer focus:outline-none"
                                            >
                                                <option value="low" className="bg-[#1a1a2e] text-white">🟢 Low</option>
                                                <option value="medium" className="bg-[#1a1a2e] text-white">🟡 Medium</option>
                                                <option value="high" className="bg-[#1a1a2e] text-white">🟠 High</option>
                                                <option value="urgent" className="bg-[#1a1a2e] text-white">🔴 Urgent</option>
                                            </select>

                                            {/* Delete button */}
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDeleteConversation(conv.id); }}
                                                className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                                title="Delete conversation"
                                            >
                                                <Trash2 size={13} />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* ── COL 3: Chat window area ───────────────────────────────────── */}
            <div
                className={`
                    flex-1 flex overflow-hidden min-w-0
                    ${mobileView === "list" ? "hidden sm:flex" : "flex"}
                `}
            >
                <AnimatePresence mode="wait">
                    {selectedConvId && selectedConv ? (
                        <motion.div
                            key={selectedConvId}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.15 }}
                            className="flex-1 flex overflow-hidden min-w-0"
                        >
                            {/* Chat window */}
                            <div className="flex-1 flex flex-col overflow-hidden min-w-0 bg-[var(--background)]">
                                <ChatWindow
                                    conversationId={selectedConvId}
                                    customerName={selectedConv.customer_name}
                                    platform={selectedConv.platform}
                                    customerId={selectedConv.customer_id}
                                    aiMode={aiMode}
                                    onBack={() => setMobileView("list")}
                                    showCustomerPanel={showCustomerPanel}
                                    onToggleCustomerPanel={() => setShowCustomerPanel(v => !v)}
                                />
                            </div>

                            {/* Customer sidebar (right panel) */}
                            {showCustomerPanel && selectedConv.customer_id && (
                                <div className="w-[300px] xl:w-[320px] shrink-0 hidden lg:flex flex-col border-l border-[var(--border)] bg-[var(--surface)] overflow-hidden">
                                    <CustomerSidebar
                                        customerId={selectedConv.customer_id}
                                        platform={selectedConv.platform}
                                        conv={selectedConv}
                                    />
                                </div>
                            )}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="empty"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex-1 flex flex-col items-center justify-center gap-4 bg-[var(--background)]"
                        >
                            <div className="w-20 h-20 rounded-3xl bg-[#6D4AE2]/10 border border-[#6D4AE2]/20 flex items-center justify-center">
                                <Zap size={32} className="text-[#6D4AE2] opacity-70" />
                            </div>
                            <div className="text-center">
                                <h2 className="text-[16px] font-semibold text-[var(--text-primary)] mb-1">
                                    Select a conversation
                                </h2>
                                <p className="text-[12.5px] text-[var(--text-secondary)]">
                                    Pick a chat from the list to start replying
                                </p>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                                {(["whatsapp", "facebook", "instagram"] as PlatformKey[]).map(p => (
                                    <div
                                        key={p}
                                        className="w-9 h-9 rounded-xl flex items-center justify-center"
                                        style={{ background: PLATFORM_CONFIG[p].bg, color: PLATFORM_CONFIG[p].color }}
                                    >
                                        <PlatformIcon platform={p} size={16} />
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
