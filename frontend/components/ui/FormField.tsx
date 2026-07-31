"use client";

import { ReactNode } from "react";

interface FormFieldProps {
  id: string;
  label: string;
  children: ReactNode;
  hint?: ReactNode;
  className?: string;
  labelAction?: ReactNode;
}

export default function FormField({
  id,
  label,
  children,
  hint,
  className = "",
  labelAction,
}: FormFieldProps) {
  return (
    <div className={className}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <label htmlFor={id} className="ds-label">
          {label}
        </label>
        {labelAction}
      </div>
      {children}
      {hint ? <div className="mt-2">{hint}</div> : null}
    </div>
  );
}
