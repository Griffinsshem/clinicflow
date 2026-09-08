"use client";

import { useId } from "react";

import { cx } from "@/lib/utils";


const CONTROL =
  "w-full h-9 px-3 rounded-[--radius-md] bg-surface text-ink " +
  "border border-line placeholder:text-ink-subtle " +
  "transition-colors duration-150 " +
  "focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent " +
  "disabled:bg-ground disabled:text-ink-muted";

const CONTROL_ERROR = "border-brick focus:border-brick focus:ring-brick";

interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: (props: {
    id: string;
    className: string;
    "aria-invalid"?: true;
    "aria-describedby"?: string;
  }) => React.ReactNode;
}

export function Field({ label, error, hint, required, children }: FieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const describedBy = [error && errorId, hint && hintId]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
        {required && <span aria-hidden="true" className="text-ink-subtle"> *</span>}
      </label>

      {children({
        id,
        className: cx(CONTROL, error && CONTROL_ERROR),
        "aria-invalid": error ? true : undefined,
        "aria-describedby": describedBy || undefined,
      })}

      {hint && !error && (
        <p id={hintId} className="text-sm text-ink-muted">
          {hint}
        </p>
      )}

      {error && (
        <p id={errorId} role="alert" className="text-sm text-brick">
          {error}
        </p>
      )}
    </div>
  );
}

export const controlClass = CONTROL;
