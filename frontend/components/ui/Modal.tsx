"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), ' +
  'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const restoreFocusTo = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    if (open) {
      restoreFocusTo.current = document.activeElement as HTMLElement | null;
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const panel = panelRef.current;
    if (!panel) return;

    const frame = requestAnimationFrame(() => {
      const target =
        contentRef.current?.querySelector<HTMLElement>(FOCUSABLE) ?? panel;
      target.focus();
    });

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
        return;
      }

      if (event.key !== "Tab" || !panel) return;

      const focusable = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;

      const trigger = restoreFocusTo.current;
      if (trigger?.isConnected) trigger.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-40 flex items-end justify-center sm:items-center">
      <div
        aria-hidden="true"
        onClick={onClose}
        className="absolute inset-0 bg-ink/20"
      />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className="relative w-full max-w-lg max-h-[90dvh] overflow-y-auto rounded-t-lg bg-surface shadow-[--shadow-overlay] sm:rounded-lg focus:outline-none"
      >
        <header className="sticky top-0 flex items-center justify-between gap-4 border-b border-hairline bg-surface px-4 py-3">
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1 text-ink-muted transition-colors hover:bg-ground hover:text-ink"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div ref={contentRef} className="p-4 pb-6 sm:pb-4">
          {children}
        </div>
      </div>
    </div>,
    document.body,
  );
}
