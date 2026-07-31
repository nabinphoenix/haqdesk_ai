"use client";

import { InputHTMLAttributes, useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import FormField from "./FormField";

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  hint?: React.ReactNode;
  labelAction?: React.ReactNode;
  fieldClassName?: string;
}

export default function PasswordField({
  label,
  hint,
  labelAction,
  fieldClassName = "",
  id,
  className = "",
  ...inputProps
}: PasswordFieldProps) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const [visible, setVisible] = useState(false);

  return (
    <FormField
      id={inputId}
      label={label}
      hint={hint}
      labelAction={labelAction}
      className={fieldClassName}
    >
      <div className="relative">
        <input
          {...inputProps}
          id={inputId}
          type={visible ? "text" : "password"}
          className={`ds-input pr-12 ${className}`}
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-[var(--radius-control)] text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--accent-glow)]"
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          aria-pressed={visible}
        >
          {visible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
        </button>
      </div>
    </FormField>
  );
}
