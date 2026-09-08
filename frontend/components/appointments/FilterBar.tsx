"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/Button";

export interface AppointmentFilters {
  date_from: string;
  date_to: string;
  status: string;
  appointment_type: string;
}

const SELECT =
  "h-9 rounded-md border border-line bg-surface px-2 text-ink " +
  "transition-colors focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

export function FilterBar({
  filters,
  onChange,
  onClear,
}: {
  filters: AppointmentFilters;
  onChange: (changes: Partial<AppointmentFilters>) => void;
  onClear: () => void;
}) {
  const hasFilters =
    Boolean(filters.status) ||
    Boolean(filters.appointment_type) ||
    Boolean(filters.date_to) ||
    Boolean(filters.date_from);

  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1">
        <span className="text-sm text-ink-muted">From</span>
        <input
          type="date"
          value={filters.date_from}
          onChange={(event) => onChange({ date_from: event.target.value })}
          className={SELECT}
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-ink-muted">To</span>
        <input
          type="date"
          value={filters.date_to}
          onChange={(event) => onChange({ date_to: event.target.value })}
          className={SELECT}
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-ink-muted">Status</span>
        <select
          value={filters.status}
          onChange={(event) => onChange({ status: event.target.value })}
          className={SELECT}
        >
          <option value="">Any status</option>
          <option value="scheduled">Scheduled</option>
          <option value="confirmed">Confirmed</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No show</option>
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-ink-muted">Type</span>
        <select
          value={filters.appointment_type}
          onChange={(event) => onChange({ appointment_type: event.target.value })}
          className={SELECT}
        >
          <option value="">Any type</option>
          <option value="consultation">Consultation</option>
          <option value="check_up">Check-up</option>
          <option value="follow_up">Follow-up</option>
          <option value="other">Other</option>
        </select>
      </label>

      {hasFilters && (
        <Button size="sm" onClick={onClear}>
          <X className="h-3.5 w-3.5" aria-hidden="true" />
          Clear
        </Button>
      )}
    </div>
  );
}
