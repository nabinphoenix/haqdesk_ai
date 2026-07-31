"use client";

import { useEffect, useId, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
    isDangerous?: boolean;
    isPending?: boolean;
}

export default function ConfirmModal({
    isOpen,
    title,
    message,
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    onConfirm,
    onCancel,
    isDangerous = true,
    isPending = false,
}: ConfirmModalProps) {
    const dialogRef = useRef<HTMLDivElement>(null);
    const cancelButtonRef = useRef<HTMLButtonElement>(null);
    const titleId = useId();
    const descriptionId = useId();

    useEffect(() => {
        if (!isOpen) return;
        const previousFocus = document.activeElement as HTMLElement | null;
        cancelButtonRef.current?.focus();

        const handler = (e: KeyboardEvent) => {
            if (e.key === "Escape" && !isPending) {
                e.preventDefault();
                onCancel();
                return;
            }
            if (e.key !== "Tab" || !dialogRef.current) return;

            const focusable = Array.from(
                dialogRef.current.querySelectorAll<HTMLElement>(
                    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
                )
            );
            if (!focusable.length) {
                e.preventDefault();
                dialogRef.current.focus();
                return;
            }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        };
        document.addEventListener("keydown", handler);
        return () => {
            document.removeEventListener("keydown", handler);
            previousFocus?.focus();
        };
    }, [isOpen, isPending, onCancel]);

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.18 }}
                    className="fixed inset-0 z-[9999] flex items-center justify-center px-4"
                    style={{ background: "rgba(9, 5, 20, 0.75)", backdropFilter: "blur(8px)" }}
                    onClick={() => { if (!isPending) onCancel(); }}
                >
                    <motion.div
                        ref={dialogRef}
                        role="alertdialog"
                        aria-modal="true"
                        aria-labelledby={titleId}
                        aria-describedby={descriptionId}
                        aria-busy={isPending}
                        tabIndex={-1}
                        initial={{ opacity: 0, scale: 0.92, y: 16 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.92, y: 16 }}
                        transition={{ duration: 0.22, ease: [0.34, 1.56, 0.64, 1] }}
                        className="w-full max-w-[400px] rounded-2xl border shadow-2xl overflow-hidden"
                        style={{
                            background: "linear-gradient(135deg, #1a1230 0%, #130e22 100%)",
                            borderColor: isDangerous ? "rgba(239,68,68,0.25)" : "rgba(109,74,226,0.25)",
                            boxShadow: isDangerous
                                ? "0 25px 60px rgba(239,68,68,0.18), 0 0 0 1px rgba(239,68,68,0.1)"
                                : "0 25px 60px rgba(109,74,226,0.18), 0 0 0 1px rgba(109,74,226,0.1)",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Top accent bar */}
                        <div
                            className="h-0.5 w-full"
                            style={{
                                background: isDangerous
                                    ? "linear-gradient(90deg, transparent, rgba(239,68,68,0.7), transparent)"
                                    : "linear-gradient(90deg, transparent, rgba(109,74,226,0.7), transparent)",
                            }}
                        />

                        <div className="p-6">
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                                        style={{
                                            background: isDangerous ? "rgba(239,68,68,0.12)" : "rgba(109,74,226,0.12)",
                                            border: isDangerous ? "1px solid rgba(239,68,68,0.25)" : "1px solid rgba(109,74,226,0.25)",
                                        }}
                                    >
                                        <AlertTriangle
                                            size={18}
                                            style={{ color: isDangerous ? "#EF4444" : "#6D4AE2" }}
                                        />
                                    </div>
                                    <h3 id={titleId} className="text-[15px] font-bold text-white tracking-tight">{title}</h3>
                                </div>
                                <button
                                    onClick={onCancel}
                                    disabled={isPending}
                                    aria-label="Close confirmation dialog"
                                    className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-all shrink-0 ml-2"
                                >
                                    <X size={14} />
                                </button>
                            </div>

                            {/* Message */}
                            <p id={descriptionId} className="text-[13px] text-gray-400 leading-relaxed pl-[52px]">
                                {message}
                            </p>

                            {/* Divider */}
                            <div className="h-px bg-white/[0.06] my-5" />

                            {/* Buttons */}
                            <div className="flex items-center gap-3 justify-end">
                                <button
                                    ref={cancelButtonRef}
                                    onClick={onCancel}
                                    disabled={isPending}
                                    className="px-4 py-2 rounded-xl text-[12px] font-semibold text-gray-300 hover:text-white hover:bg-white/10 transition-all border border-white/10"
                                >
                                    {cancelLabel}
                                </button>
                                <button
                                    onClick={onConfirm}
                                    disabled={isPending}
                                    className="px-5 py-2 rounded-xl text-[12px] font-bold text-white transition-all active:scale-95"
                                    style={{
                                        background: isDangerous
                                            ? "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)"
                                            : "linear-gradient(135deg, #6D4AE2 0%, #5B3BC7 100%)",
                                        boxShadow: isDangerous
                                            ? "0 4px 14px rgba(220,38,38,0.35)"
                                            : "0 4px 14px rgba(109,74,226,0.35)",
                                    }}
                                >
                                    {confirmLabel}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
