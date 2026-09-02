"use client";

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
} from "react";
import { usePathname } from "next/navigation";
import { toast } from "sonner";
import { fetchWithAuth } from "@/lib/api";

export const INBOX_CONVERSATIONS_UPDATED_EVENT = "haqdesk:inbox-conversations-updated";

const POLL_INTERVAL_MS = 3000;
const NOTIFICATION_SOUND_PATH = "/audio/sound_notification_haqdeskAI.mp3";

type InboxConversationSnapshot = {
    id: number | string;
    time?: string | null;
    last_message_sender_type?: string | null;
    last_message?: string | null;
    customer_name?: string | null;
    unread?: number | null;
};

type NotificationContextValue = {
    setActiveConversationId: (conversationId: number | null) => void;
};

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function useBackgroundNotifications() {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error("useBackgroundNotifications must be used inside BackgroundNotificationProvider");
    }
    return context;
}

function isPublicPath(pathname: string) {
    return pathname === "/" || [
        "/login",
        "/register",
        "/accept-invite",
        "/forgot-password",
        "/reset-password",
        "/onboarding/business",
    ].some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export default function BackgroundNotificationProvider({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const activeConversationIdRef = useRef<number | null>(null);
    const previousConversationStateRef = useRef<Map<number, { time: string; unread: number }>>(new Map());
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const audioUnlockedRef = useRef(false);
    const pendingSoundRef = useRef(false);

    const setActiveConversationId = useCallback((conversationId: number | null) => {
        activeConversationIdRef.current = conversationId;
    }, []);

    const contextValue = useMemo(() => ({ setActiveConversationId }), [setActiveConversationId]);

    const playNotificationSound = useCallback(() => {
        const audio = audioRef.current;
        if (!audio) {
            pendingSoundRef.current = true;
            return;
        }

        audio.pause();
        audio.currentTime = 0;
        const playPromise = audio.play();
        playPromise?.catch((error) => {
            // Browsers reject playback until the user has interacted with the
            // site. Keep the notification pending so the first interaction
            // after it arrives can play it.
            pendingSoundRef.current = true;
            console.warn("Notification sound could not play:", error);
        });
    }, []);

    // Prime the audio element from a real user gesture. This avoids the
    // intermittent autoplay failures that occur when the first notification
    // arrives while the app is in a background tab.
    useEffect(() => {
        const audio = new Audio(NOTIFICATION_SOUND_PATH);
        audio.preload = "auto";
        audio.volume = 0.6;
        audioRef.current = audio;

        const unlockAudio = () => {
            if (audioUnlockedRef.current) return;

            const wasMuted = audio.muted;
            const hadPendingSound = pendingSoundRef.current;
            audio.muted = true;
            const unlockPromise = audio.play();

            const finishUnlock = () => {
                audio.pause();
                audio.currentTime = 0;
                audio.muted = wasMuted;
                audioUnlockedRef.current = true;

                if (hadPendingSound || pendingSoundRef.current) {
                    pendingSoundRef.current = false;
                    playNotificationSound();
                }
            };

            if (unlockPromise) {
                unlockPromise.then(finishUnlock).catch(() => {
                    audio.muted = wasMuted;
                });
            } else {
                finishUnlock();
            }
        };

        const interactionEvents: Array<keyof WindowEventMap> = ["pointerdown", "keydown", "touchstart"];
        interactionEvents.forEach((eventName) => {
            window.addEventListener(eventName, unlockAudio, { capture: true, passive: true });
        });

        return () => {
            interactionEvents.forEach((eventName) => {
                window.removeEventListener(eventName, unlockAudio, { capture: true });
            });
            audio.pause();
            audioRef.current = null;
        };
    }, [playNotificationSound]);

    useEffect(() => {
        if (isPublicPath(pathname) || !localStorage.getItem("token")) return;

        let stopped = false;
        let requestInFlight = false;
        let timer: number | undefined;

        const scheduleNextPoll = () => {
            if (!stopped) timer = window.setTimeout(runPoll, POLL_INTERVAL_MS);
        };

        const runPoll = async () => {
            if (stopped || requestInFlight) return;
            requestInFlight = true;

            try {
                const response = await fetchWithAuth(
                    `/api/v1/inbox/conversations?t=${Date.now()}`,
                    { cache: "no-store" },
                );

                if (!response.ok || stopped) return;

                const data = await response.json() as InboxConversationSnapshot[];
                const currentIds = new Set<number>();
                const newCustomerMessages: InboxConversationSnapshot[] = [];

                data.forEach((conversation) => {
                    const conversationId = Number(conversation.id);
                    const currentTime = String(conversation.time ?? "");
                    const currentUnread = Number(conversation.unread ?? 0);
                    const previousState = previousConversationStateRef.current.get(conversationId);
                    const hasNewCustomerMessage = previousState !== undefined && (
                        currentUnread > previousState.unread ||
                        (
                            previousState.time !== currentTime &&
                            conversation.last_message_sender_type === "customer"
                        )
                    );
                    const isViewingThisConversation =
                        pathname === "/inbox" && activeConversationIdRef.current === conversationId;
                    const shouldNotify =
                        document.visibilityState !== "visible" || !isViewingThisConversation;

                    currentIds.add(conversationId);
                    if (hasNewCustomerMessage && shouldNotify) {
                        newCustomerMessages.push(conversation);
                    }
                    previousConversationStateRef.current.set(conversationId, {
                        time: currentTime,
                        unread: currentUnread,
                    });
                });

                previousConversationStateRef.current.forEach((_state, conversationId) => {
                    if (!currentIds.has(conversationId)) {
                        previousConversationStateRef.current.delete(conversationId);
                    }
                });

                if (newCustomerMessages.length > 0) {
                    playNotificationSound();
                    newCustomerMessages.forEach((conversation) => {
                        const previewText = conversation.last_message || "New message received";
                        const senderName = conversation.customer_name || "Customer";
                        toast.info(`New message from ${senderName}`, {
                            description: previewText.substring(0, 50) + (previewText.length > 50 ? "..." : ""),
                            duration: 5000,
                            action: {
                                label: "View",
                                onClick: () => window.dispatchEvent(
                                    new CustomEvent("haqdesk:open-conversation", {
                                        detail: Number(conversation.id),
                                    }),
                                ),
                            },
                        });
                    });
                }

                window.dispatchEvent(
                    new CustomEvent(INBOX_CONVERSATIONS_UPDATED_EVENT, { detail: data }),
                );
            } catch (error) {
                if (!stopped) console.warn("Background inbox notification poll failed:", error);
            } finally {
                requestInFlight = false;
                scheduleNextPoll();
            }
        };

        const handleVisibilityChange = () => {
            if (!document.hidden) {
                if (timer !== undefined) window.clearTimeout(timer);
                void runPoll();
            }
        };

        void runPoll();
        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            stopped = true;
            requestInFlight = false;
            if (timer !== undefined) window.clearTimeout(timer);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, [pathname, playNotificationSound]);

    return (
        <NotificationContext.Provider value={contextValue}>
            {children}
        </NotificationContext.Provider>
    );
}
