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
                    style={{ background: "color-mix(in srgb, var(--text-primary) 55%, transparent)", backdropFilter: "blur(8px)" }}
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
                        className="w-full max-w-[400px] rounded-2xl border bg-surface shadow-2xl overflow-hidden"
                        style={{
                            borderColor: isDangerous ? "var(--error-border)" : "var(--border)",
                            boxShadow: "var(--shadow-modal)",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Top accent bar */}
                        <div
                            className="h-0.5 w-full"
                            style={{
                                background: isDangerous
                                    ? "var(--error)"
                                    : "var(--accent)",
                            }}
                        />

                        <div className="p-6">
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                                        style={{
                                            background: isDangerous ? "var(--error-surface)" : "color-mix(in srgb, var(--accent) 12%, transparent)",
                                            border: `1px solid ${isDangerous ? "var(--error-border)" : "var(--border)"}`,
                                        }}
                                    >
                                        <AlertTriangle
                                            size={18}
                                            style={{ color: isDangerous ? "var(--error-foreground)" : "var(--accent)" }}
                                        />
                                    </div>
                                    <h3 id={titleId} className="text-[15px] font-bold text-foreground tracking-tight">{title}</h3>
                                </div>
                                <button
                                    onClick={onCancel}
                                    disabled={isPending}
                                    aria-label="Close confirmation dialog"
                                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-wash transition-all shrink-0 ml-2"
                                >
                                    <X size={14} />
                                </button>
                            </div>

                            {/* Message */}
                            <p id={descriptionId} className="text-[13px] text-muted-foreground leading-relaxed pl-[52px]">
                                {message}
                            </p>

                            {/* Divider */}
                            <div className="h-px bg-surface/[0.06] my-5" />

                            {/* Buttons */}
                            <div className="flex items-center gap-3 justify-end">
                                <button
                                    ref={cancelButtonRef}
                                    onClick={onCancel}
                                    disabled={isPending}
                                    className="px-4 py-2 rounded-xl text-[12px] font-semibold text-muted-foreground hover:text-foreground hover:bg-surface-wash transition-all border border-border"
                                >
                                    {cancelLabel}
                                </button>
                                <button
                                    onClick={onConfirm}
                                    disabled={isPending}
                                    className={`px-5 py-2 rounded-xl text-[12px] font-bold text-on-accent transition-all active:scale-95 ${isDangerous ? "bg-[var(--error)]" : "bg-accent hover:bg-accent-hover"}`}
                                    style={{
                                        boxShadow: "var(--shadow-card)",
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
