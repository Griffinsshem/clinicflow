"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { ApiError, api } from "@/lib/client";
import { humanise } from "@/lib/format";
import { useToast } from "@/providers/ToastProvider";
import type { Appointment, AppointmentStatus } from "@/types/api";

const NEXT_STATUSES: Record<AppointmentStatus, AppointmentStatus[]> = {
  scheduled: ["confirmed", "completed", "cancelled", "no_show"],
  confirmed: ["completed", "cancelled", "no_show"],
  completed: [],
  cancelled: [],
  no_show: ["scheduled"],
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

  const options = NEXT_STATUSES[appointment.status];
  if (options.length === 0) return null;

  async function setStatus(status: AppointmentStatus) {
    setWorking(status);
    try {
      await api.patch(`/appointments/${appointment.id}`, { status });
      toast(`Marked ${humanise(status).toLowerCase()}.`);
      onChanged();
    } catch (error) {
      toast(
        error instanceof ApiError ? error.message : "Couldn't update the appointment.",
        "error",
      );
    } finally {
      setWorking(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((status) => (
        <Button
          key={status}
          size="sm"
          loading={working === status}
          disabled={working !== null}
          onClick={() => setStatus(status)}
        >
          {humanise(status)}
        </Button>
      ))}
    </div>
  );
}
