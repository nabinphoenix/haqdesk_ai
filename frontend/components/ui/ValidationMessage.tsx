"use client";

import { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";

type ValidationTone = "neutral" | "success" | "error" | "warning";

const styles: Record<ValidationTone, string> = {
  neutral: "text-[var(--text-secondary)]",
  success: "text-[var(--success-foreground)]",
  error: "text-[var(--error-foreground)]",
  warning: "text-[var(--warning)]",
};

const icons = {
  neutral: Info,
  success: CheckCircle2,
  error: AlertCircle,
  warning: TriangleAlert,
};

export default function ValidationMessage({
  tone = "neutral",
  children,
  id,
}: {
  tone?: ValidationTone;
  children: ReactNode;
  id?: string;
}) {
  const Icon = icons[tone];
  return (
    <div id={id} className={`flex items-start gap-2 text-xs leading-[1.125rem] ${styles[tone]}`}>
      <Icon size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
