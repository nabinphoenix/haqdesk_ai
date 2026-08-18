"use client";

import { useState, useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import AISuggestionBox from "./AISuggestionBox";
import { fetchWithAuth } from "@/lib/api";
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
    Mic,
} from "lucide-react";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const formatMessageDate = (date: Date): string => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const isSameDay = (d1: Date, d2: Date) =>
        d1.getDate() === d2.getDate() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getFullYear() === d2.getFullYear();

    if (isSameDay(date, today)) return "Today";
    if (isSameDay(date, yesterday)) return "Yesterday";
    return date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
};

// ── Types ──────────────────────────────────────────────────────────────────────
interface Message {
    id: number;
    content: string;
    sender: "customer" | "agent" | "ai";
    sender_name?: string | null;
    message_type?: string;
    timestamp: string;
    rawDate: Date;
    ai_draft?: string | null;
    ai_language?: string | null;
    sentiment?: string | null;
    ai_metadata?: any;
    isVoice?: boolean;
    audioUrl?: string;
}

interface ChatWindowProps {
    conversationId: number | null;
    customerName?: string;
    platform?: string;
    customerId?: string;
    aiMode?: "auto" | "review";
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
    aiMode = "review",
    onBack,
    showCustomerPanel,
    onToggleCustomerPanel,
}: ChatWindowProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isAiAssistedReply, setIsAiAssistedReply] = useState(false);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [sending, setSending] = useState(false);
    const [emailSubject, setEmailSubject] = useState("Re: Support from TechSuru");
    const [conversationPlatform, setConversationPlatform] = useState<string>(platform || "");
    const [conversationStatus, setConversationStatus] = useState<string>("open");
    const [conversationPriority, setConversationPriority] = useState<string>("medium");
    const [uploadingFile, setUploadingFile] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [recordingDuration, setRecordingDuration] = useState(0);
    const [attachedFile, setAttachedFile] = useState<File | null>(null);

    const scrollRef   = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const emojiRef    = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const recordingTimerRef = useRef<any | null>(null);

    // AI suggestion state
    const [aiSuggestion, setAiSuggestion] = useState<Message | null>(null);
    const [aiDismissed, setAiDismissed] = useState(false);
    const prevSuggestionId = useRef<number | null>(null);

    const pColor = PLATFORM_CONFIG[platform?.toLowerCase() || ""]?.color || "#6D4AE2";
    const pLabel = PLATFORM_CONFIG[platform?.toLowerCase() || ""]?.label || platform || "Chat";

    const fetchMessages = async () => {
        if (!conversationId) return;
        try {
            const res = await fetchWithAuth(
                `/api/v1/inbox/conversations/${conversationId}/messages?t=${Date.now()}`,
                { cache: "no-store" }
            );
            if (!res.ok) return;
            const data = await res.json();
            const formatted: Message[] = data.map((m: any) => {
                const dateObj = new Date(m.timestamp);
                return {
                    id: m.id,
                    content: m.content,
                    sender: m.sender_type,
                    sender_name: m.sender_name || null,
                    message_type: m.message_type || "text",
                    timestamp: dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    rawDate: dateObj,
                    ai_draft: m.ai_draft || null,
                    ai_language: m.ai_language || null,
                    sentiment: m.sentiment || null,
                    ai_metadata: m.ai_metadata || null,
                    isVoice: m.message_type === "voice",
                    audioUrl: m.ai_metadata?.audio_url || (m.message_type === "voice" ? m.content : undefined),
                };
            });
            setMessages(prev => {
                const optimisticMessages = prev.filter(p =>
                    p.id > 1700000000000 &&
                    !formatted.some(f => f.content === p.content && f.sender === p.sender)
                );
                const merged = [...formatted, ...optimisticMessages];
                
                if (prev.length === merged.length) {
                    const hasDifference = prev.some((m, idx) => 
                        m.id !== merged[idx].id || m.content !== merged[idx].content
                    );
                    if (!hasDifference) return prev;
                }
                return merged;
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

    // AI suggestion logic (only active in Review Mode)
    useEffect(() => {
        if (aiMode === "auto") {
            setAiSuggestion(null);
            return;
        }
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
    }, [messages, aiMode]);

    // Reset on conversation change
    useEffect(() => {
        setAiDismissed(false);
        setAiSuggestion(null);
        prevSuggestionId.current = null;
        setInput("");
        setMessages([]);
        setConversationPlatform(platform?.toLowerCase() || "");
        setEmailSubject("Re: Support from TechSuru");
    }, [conversationId]);

    useEffect(() => {
        if (!conversationId) return;
        const fetchConvDetails = async () => {
            try {
                const res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}`);
                if (res.ok) {
                    const data = await res.json();
                    setConversationStatus(data.status || "open");
                    setConversationPriority(data.priority || "medium");
                }
            } catch (e) { console.error(e); }
        };
        fetchConvDetails();
    }, [conversationId]);

    const handleUpdateStatus = async (status: string) => {
        try {
            const res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status }),
            });
            if (res.ok) {
                setConversationStatus(status);
                toast.success(`Marked as ${status}`);
                // Dispatch event to trigger refresh in parent conversation list
                window.dispatchEvent(new Event("customerLinked"));
            }
        } catch (e) { console.error(e); }
    };

    const handleUpdatePriority = async (priority: string) => {
        try {
            const res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ priority }),
            });
            if (res.ok) {
                setConversationPriority(priority);
                toast.success(`Priority set to ${priority}`);
                // Dispatch event to trigger refresh in parent conversation list
                window.dispatchEvent(new Event("customerLinked"));
            }
        } catch (e) { console.error(e); }
    };

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

    // Cleanup recording timer on unmount
    useEffect(() => {
        return () => {
            if (recordingTimerRef.current) {
                clearInterval(recordingTimerRef.current);
            }
        };
    }, []);

    // ── Voice Recording Handlers ───────────────────────────────────────────
    const startRecording = async () => {
        try {
            if (recordingTimerRef.current) {
                clearInterval(recordingTimerRef.current);
                recordingTimerRef.current = null;
            }

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            setRecordingDuration(0);

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                stream.getTracks().forEach(track => track.stop());
                await sendVoiceMessage(audioBlob);
            };

            mediaRecorder.start(100);
            setIsRecording(true);

            // Timer to show recording duration
            recordingTimerRef.current = setInterval(() => {
                setRecordingDuration(prev => {
                    if (prev >= 120) {
                        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
                            mediaRecorderRef.current.stop();
                        }
                        setIsRecording(false);
                        if (recordingTimerRef.current) {
                            clearInterval(recordingTimerRef.current);
                            recordingTimerRef.current = null;
                        }
                        return 0;
                    }
                    return prev + 1;
                });
            }, 1000);

        } catch (err) {
            toast.error("Microphone access denied. Please allow microphone access.");
            console.error("Recording error:", err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop();
        }
        setIsRecording(false);
        setRecordingDuration(0);
        if (recordingTimerRef.current) {
            clearInterval(recordingTimerRef.current);
            recordingTimerRef.current = null;
        }
    };

    const cancelRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.ondataavailable = null;
            mediaRecorderRef.current.onstop = null;
            if (mediaRecorderRef.current.state === "recording") {
                mediaRecorderRef.current.stop();
            }
            if (mediaRecorderRef.current.stream) {
                mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            }
        }
        setIsRecording(false);
        setRecordingDuration(0);
        audioChunksRef.current = [];
        if (recordingTimerRef.current) {
            clearInterval(recordingTimerRef.current);
            recordingTimerRef.current = null;
        }
    };

    const sendVoiceMessage = async (audioBlob: Blob) => {
        if (!conversationId) return;
        setUploadingFile(true);

        try {
            const formData = new FormData();
            const filename = `voice_message_${Date.now()}.webm`;
            formData.append("file", audioBlob, filename);
            formData.append("conversation_id", conversationId.toString());
            formData.append("message_type", "voice");

            const token = localStorage.getItem("token");
            const res = await fetch(
                `${API_URL}/api/v1/inbox/conversations/${conversationId}/attachment`,
                {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` },
                    body: formData,
                }
            );

            if (res.ok) {
                const data = await res.json();
                const now = new Date();
                setMessages(prev => [...prev, {
                    id: data.message_id || Date.now(),
                    content: `🎤 Voice message`,
                    sender: "agent",
                    sender_name: localStorage.getItem("userName") || "Agent",
                    timestamp: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    rawDate: now,
                    isVoice: true,
                    audioUrl: data.audio_url,
                }]);
                toast.success("Voice message sent");
            } else {
                toast.error("Failed to send voice message");
            }
        } catch (e) {
            toast.error("Network error sending voice message");
        } finally {
            setUploadingFile(false);
        }
    };

    // ── Send message ───────────────────────────────────────────────────────
    const handleSend = async () => {
        if ((!input.trim() && !attachedFile) || !conversationId || sending) return;
        const token = localStorage.getItem("token");
        if (!token) { alert("Session expired. Please login."); return; }

        const text = input.trim();
        const aiAssisted = isAiAssistedReply;
        const fileToSend = attachedFile;

        setInput("");
        setIsAiAssistedReply(false);
        setAttachedFile(null);
        setSending(true);

        const tempId = Date.now();
        const currentUserName = localStorage.getItem("userName") || "Agent";
        const now = new Date();

        if (fileToSend) {
            const formData = new FormData();
            formData.append("file", fileToSend);
            formData.append("conversation_id", conversationId.toString());
            if (text) {
                formData.append("message", text);
            }
            if (conversationPlatform === "email") {
                formData.append("subject", emailSubject);
            }

            // Optimistic rendering
            setMessages(prev => {
                const tempMsgs = [...prev];
                tempMsgs.push({
                    id: tempId,
                    content: `/uploads/attachments/${fileToSend.name}`,
                    message_type: fileToSend.type.startsWith("image/") ? "image" : fileToSend.type.startsWith("video/") ? "video" : "file",
                    ai_metadata: { filename: fileToSend.name },
                    sender: "agent",
                    sender_name: currentUserName,
                    timestamp: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    rawDate: now,
                });
                if (text) {
                    tempMsgs.push({
                        id: tempId + 1,
                        content: text,
                        sender: "agent",
                        sender_name: currentUserName,
                        timestamp: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                        rawDate: now,
                    });
                }
                return tempMsgs;
            });

            try {
                const res = await fetch(`${API_URL}/api/v1/inbox/conversations/${conversationId}/attachment`, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` },
                    body: formData,
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.delivered === false) {
                        toast.error(`Delivery failed: ${data.error || "Platform error"}`);
                        setMessages(prev => prev.filter(m => m.id !== tempId && m.id !== tempId + 1));
                    } else {
                        toast.success("Attachment sent successfully");
                    }
                    fetchMessages();
                } else {
                    const errData = await res.json().catch(() => ({}));
                    const errMsg = errData.detail || "Failed to send attachment";
                    toast.error(
                        res.status === 409
                            ? `${errMsg} Open Settings → Integrations to connect it.`
                            : errMsg
                    );
                    setMessages(prev => prev.filter(m => m.id !== tempId && m.id !== tempId + 1));
                }
            } catch (e) {
                toast.error("Network error uploading attachment");
                setMessages(prev => prev.filter(m => m.id !== tempId && m.id !== tempId + 1));
            } finally {
                setSending(false);
            }
        } else {
            // Optimistic
            setMessages(prev => [...prev, {
                id: tempId,
                content: text,
                sender: "agent",
                sender_name: currentUserName,
                timestamp: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                rawDate: now,
            }]);

            try {
                let res: Response;
                res = await fetchWithAuth(`/api/v1/inbox/conversations/${conversationId}/reply`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        content: text,
                        subject: conversationPlatform === "email" ? emailSubject : undefined,
                        ai_assisted: aiAssisted,
                    }),
                });
                if (res.ok) {
                    const savedMessage = await res.json();
                    
                    if (savedMessage.error) {
                        toast.error(`Message saved but not delivered: ${savedMessage.error}`);
                    }

                    setMessages(prev => prev.map(m =>
                        m.id === tempId
                            ? {
                                id: savedMessage.id,
                                content: savedMessage.content,
                                sender: savedMessage.sender_type,
                                sender_name: currentUserName,
                                timestamp: new Date(savedMessage.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                                rawDate: new Date(savedMessage.timestamp),
                                ai_draft: null,
                                ai_language: null,
                                sentiment: null,
                              }
                            : m
                    ));
                    fetchMessages();
                } else {
                    const errData = await res.json().catch(() => ({}));
                    const errMsg = errData.detail || "Failed to send message";
                    toast.error(errMsg);
                    setMessages(prev => prev.filter(m => m.id !== tempId));
                }
            } catch (e) {
                toast.error("Network error sending message");
                setMessages(prev => prev.filter(m => m.id !== tempId));
            } finally {
                setSending(false);
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    const handleFileAttachment = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !conversationId) return;

        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            toast.error("File too large. Maximum size is 10MB.");
            return;
        }

        setAttachedFile(file);
        if (fileInputRef.current) fileInputRef.current.value = "";
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
                            className="sm:hidden w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:bg-surface-wash dark:hover:bg-surface-wash transition-all"
                        >
                            <ChevronLeft size={18} />
                        </button>
                    )}

                    {/* Avatar */}
                    <div className="relative w-9 h-9 shrink-0">
                        <div
                            className="w-full h-full rounded-xl flex items-center justify-center text-foreground text-[12px] font-bold"
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
                                className="px-2 py-0.5 rounded-full text-foreground text-[9px] font-bold flex items-center gap-1"
                                style={{ background: pColor }}
                            >
                                <PlatformIcon platform={platform || ""} size={8} />
                                {pLabel}
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] inline-block" />
                            <span className="text-[10px] text-[var(--text-secondary)]">Active now</span>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                    {/* Status toggle */}
                    <select
                        value={conversationStatus || "open"}
                        onChange={(e) => handleUpdateStatus(e.target.value)}
                        className="text-[10px] font-bold px-2 py-1 rounded-lg bg-surface-wash border border-[var(--border)] text-[var(--text-secondary)] focus:outline-none"
                    >
                        <option value="open" className="bg-[var(--surface)] text-[var(--text-primary)]">Open</option>
                        <option value="resolved" className="bg-[var(--surface)] text-[var(--text-primary)]">Resolved</option>
                        <option value="closed" className="bg-[var(--surface)] text-[var(--text-primary)]">Closed</option>
                    </select>

                    {/* Priority badge */}
                    <select
                        value={conversationPriority || "medium"}
                        onChange={(e) => handleUpdatePriority(e.target.value)}
                        className={`text-[10px] font-bold px-2 py-1 rounded-lg border focus:outline-none ${
                            conversationPriority === "urgent" ? "bg-[var(--error-surface)] border-[var(--error-border)] text-[var(--error-foreground)]" :
                            conversationPriority === "high" ? "bg-orange-500/20 border-orange-500/30 text-orange-400" :
                            conversationPriority === "low" ? "bg-[var(--success-surface)] border-[var(--success-border)] text-[var(--success-foreground)]" :
                            "bg-yellow-500/20 border-yellow-500/30 text-[var(--warning)]"
                        }`}
                    >
                        <option value="low" className="bg-[var(--surface)] text-[var(--text-primary)]">🟢 Low</option>
                        <option value="medium" className="bg-[var(--surface)] text-[var(--text-primary)]">🟡 Medium</option>
                        <option value="high" className="bg-[var(--surface)] text-[var(--text-primary)]">🟠 High</option>
                        <option value="urgent" className="bg-[var(--surface)] text-[var(--text-primary)]">🔴 Urgent</option>
                    </select>

                    {onToggleCustomerPanel && (
                        <button
                            onClick={onToggleCustomerPanel}
                            title={showCustomerPanel ? "Hide customer info" : "Show customer info"}
                            className="hidden lg:flex w-8 h-8 rounded-lg items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-wash dark:hover:bg-surface-wash transition-all"
                        >
                            {showCustomerPanel ? <PanelRightClose size={15} /> : <PanelRightOpen size={15} />}
                        </button>
                    )}
                    <button className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-wash dark:hover:bg-surface-wash transition-all">
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
                    messages.map((msg, idx) => {
                        const showDateSeparator = idx === 0 ||
                            formatMessageDate(msg.rawDate) !== formatMessageDate(messages[idx - 1].rawDate);

                        const agentInitials = msg.sender === "agent" && msg.sender_name
                            ? msg.sender_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2)
                            : msg.sender === "ai"
                            ? "AI"
                            : localStorage.getItem("userName")?.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2) || "AG";

                        return (
                            <div key={msg.id} className="space-y-3">
                                {showDateSeparator && (
                                    <div className="flex items-center justify-center my-4">
                                        <span className="text-[11px] font-medium text-[var(--text-secondary)] bg-[var(--surface-wash)] px-3 py-1 rounded-full border border-[var(--border)]">
                                            {formatMessageDate(msg.rawDate)}
                                        </span>
                                    </div>
                                )}
                                <MessageBubble
                                    {...msg}
                                    agentInitials={agentInitials}
                                    onUseDraft={(draft) => {
                                        setInput(draft);
                                        setIsAiAssistedReply(true);
                                        setTimeout(() => textareaRef.current?.focus(), 50);
                                    }}
                                />
                            </div>
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
                        onAccept={() => { setInput(aiSuggestion.content); setIsAiAssistedReply(true); setAiDismissed(true); }}
                        onEdit={() => {
                            setInput(aiSuggestion.content);
                            setIsAiAssistedReply(true);
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
                                <button onClick={() => setShowEmojiPicker(false)} className="text-[var(--text-secondary)] hover:text-[var(--error-foreground)] transition-colors">
                                    <X size={12} />
                                </button>
                            </div>
                            <div className="grid grid-cols-9 gap-1">
                                {EMOJIS.map(e => (
                                    <button
                                        key={e}
                                        onClick={() => setInput(p => p + e)}
                                        className="w-8 h-8 rounded-lg flex items-center justify-center text-[17px] hover:bg-surface-wash dark:hover:bg-surface-wash transition-all active:scale-90"
                                    >
                                        {e}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* File preview */}
                {attachedFile && (
                    <div 
                        className="flex items-center gap-3 border rounded-xl px-4 py-2.5 mb-2.5"
                        style={{ background: "var(--surface-wash)", borderColor: "var(--border)" }}
                    >
                        <div 
                            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                            style={{ background: "rgba(109, 74, 226, 0.15)", color: "#8B5CF6" }}
                        >
                            <Paperclip size={14} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-[12px] font-medium text-[var(--text-primary)] truncate">{attachedFile.name}</p>
                            <p className="text-[10px] text-[var(--text-secondary)]">
                                {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                        </div>
                        <button
                            onClick={() => setAttachedFile(null)}
                            className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--error-foreground)] hover:bg-[var(--error-surface)] rounded-lg transition-all"
                            title="Remove attachment"
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}

                <div className="flex flex-col gap-2.5">
                    {/* Show subject line only for email conversations */}
                    {conversationPlatform === "email" && !isRecording && (
                        <input
                            type="text"
                            value={emailSubject}
                            onChange={(e) => setEmailSubject(e.target.value)}
                            placeholder="Subject..."
                            className="w-full px-4 py-2 rounded-xl text-[12px] outline-none transition-all"
                            style={{
                                background: "var(--surface-wash)",
                                border: "1px solid var(--border)",
                                color: "var(--text-primary)",
                            }}
                        />
                    )}

                    {isRecording ? (
                        /* Recording mode UI */
                        <div className="flex items-center gap-3 py-2">
                            {/* Animated recording indicator */}
                            <div className="flex items-center gap-2 flex-1 bg-[var(--error-surface)] border border-[var(--error-border)] rounded-xl px-4 py-2.5">
                                <div className="w-3 h-3 rounded-full bg-[var(--error)] animate-pulse shrink-0" />
                                <span className="text-[var(--error-foreground)] text-[13px] font-medium">Recording...</span>
                                <span className="text-[var(--error-foreground)]/60 text-[12px] ml-auto">
                                    {Math.floor(recordingDuration / 60).toString().padStart(2, "0")}:
                                    {(recordingDuration % 60).toString().padStart(2, "0")}
                                </span>
                            </div>

                            {/* Cancel recording */}
                            <button
                                onClick={cancelRecording}
                                className="p-2.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-wash dark:hover:bg-surface-wash rounded-xl transition-all"
                                title="Cancel recording"
                            >
                                <X size={18} />
                            </button>

                            {/* Stop and send */}
                            <button
                                onClick={stopRecording}
                                className="p-2.5 bg-[var(--error)] hover:bg-red-600 text-on-accent rounded-xl transition-all flex items-center gap-1.5"
                                title="Stop and send"
                            >
                                <Send size={16} />
                            </button>
                        </div>
                    ) : (
                        /* Normal message input UI */
                        <>
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
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${showEmojiPicker ? "bg-accent text-on-accent" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-wash dark:hover:bg-surface-wash"}`}
                                    >
                                        <Smile size={15} />
                                    </button>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={uploadingFile}
                                        className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-wash dark:hover:bg-surface-wash transition-all disabled:opacity-50"
                                        title="Attach file"
                                    >
                                        {uploadingFile ? (
                                            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                        ) : (
                                            <Paperclip size={15} />
                                        )}
                                    </button>

                                    {/* Mic recording button - only show when input is empty and no file attached */}
                                    {!input.trim() && !attachedFile && (
                                        <button
                                            onClick={startRecording}
                                            className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-secondary)] hover:text-purple-500 hover:bg-accent/10 transition-all shrink-0"
                                            title="Record voice message"
                                        >
                                            <Mic size={15} />
                                        </button>
                                    )}

                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        onChange={handleFileAttachment}
                                        accept="image/*,.pdf,.doc,.docx,.txt,.xlsx,.csv,.mp3,.mp4,.webm,.ogg,.wav"
                                    />
                                    <span className="text-[10px] text-[var(--text-secondary)] ml-1 hidden sm:inline">
                                        Enter to send · Shift+Enter for newline
                                    </span>
                                </div>

                                <button
                                    onClick={handleSend}
                                    disabled={(!input.trim() && !attachedFile) || sending}
                                    className="flex items-center gap-2 px-5 py-2 rounded-xl text-foreground text-[12px] font-semibold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                                    style={{ background: pColor, boxShadow: `0 4px 15px ${pColor}40` }}
                                >
                                    {sending ? (
                                        <div className="w-3.5 h-3.5 border-2 border-on-accent/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <Send size={13} strokeWidth={2.5} />
                                    )}
                                    Send
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
