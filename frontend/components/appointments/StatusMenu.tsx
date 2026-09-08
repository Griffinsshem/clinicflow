"use client";

import { useEffect, useRef, useState } from "react";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { ApiError, api } from "@/lib/client";
import { humanise } from "@/lib/format";
import { cx } from "@/lib/utils";
import { useToast } from "@/providers/ToastProvider";
import type { Appointment, AppointmentStatus } from "@/types/api";


const TRANSITIONS: Record<
  AppointmentStatus,
  { primary: AppointmentStatus | null; others: AppointmentStatus[] }
> = {
  scheduled: {
    primary: "confirmed",
    others: ["completed", "cancelled", "no_show"],
  },
  confirmed: {
    primary: "completed",
    others: ["cancelled", "no_show"],
  },
  completed: { primary: null, others: [] },
  cancelled: { primary: null, others: [] },
  no_show: { primary: "scheduled", others: [] },
};

export function StatusMenu({
  appointment,
  onChanged,
}: {
  appointment: Appointment;
  onChanged: () => void;
}) {
  const toast = useToast();
  const [working, setWorking] = useState<AppointmentStatus | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const { primary, others } = TRANSITIONS[appointment.status];

  useEffect(() => {
    if (!menuOpen) return;

    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  if (!primary) return null;

  async function setStatus(status: AppointmentStatus) {
    setWorking(status);
    setMenuOpen(false);
    try {
      await api.patch(`/appointments/${appointment.id}`, { status });
      toast(`Marked ${humanise(status).toLowerCase()}.`);
      onChanged();
    } catch (error) {
      toast(
        error instanceof ApiError
          ? error.message
          : "Couldn't update the appointment.",
        "error",
      );
    } finally {
      setWorking(null);
    }
  }

  return (
    <div ref={containerRef} className="relative flex items-center gap-1">
      <Button
        size="sm"
        loading={working === primary}
        disabled={working !== null}
        onClick={() => setStatus(primary)}
      >
        {humanise(primary)}
      </Button>

      {others.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            disabled={working !== null}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-label="More status options"
            className={cx(
              "flex h-8 w-8 items-center justify-center rounded-md border border-line",
              "text-ink-muted transition-colors hover:bg-ground hover:text-ink",
              "disabled:opacity-50 disabled:pointer-events-none",
            )}
          >
            <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
          </button>

          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 top-full z-20 mt-1 min-w-40 rounded-md border border-hairline bg-surface py-1 shadow-[--shadow-overlay]"
            >
              {others.map((status) => (
                <button
                  key={status}
                  role="menuitem"
                  type="button"
                  onClick={() => setStatus(status)}
                  className="block w-full px-3 py-1.5 text-left text-sm text-ink transition-colors hover:bg-ground"
                >
                  Mark {humanise(status).toLowerCase()}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
