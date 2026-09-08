"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { ApiError, api } from "@/lib/client";
import type { FollowUp } from "@/types/api";


function defaultSlot(): string {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  date.setHours(9, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

function toIsoWithOffset(localValue: string): string {
  const offsetMinutes = -new Date(localValue).getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const pad = (n: number) => String(Math.floor(Math.abs(n))).padStart(2, "0");
  return `${localValue}:00${sign}${pad(offsetMinutes / 60)}:${pad(offsetMinutes % 60)}`;
}

export function CompleteDialog({
  followUp,
  onDone,
  onCancel,
}: {
  followUp: FollowUp | null;
  onDone: (scheduled: boolean) => void;
  onCancel: () => void;
}) {
  const [scheduleNext, setScheduleNext] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  if (!followUp) return null;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setErrors({});

    const form = new FormData(event.currentTarget);

    const payload = scheduleNext
      ? {
          scheduled_at: toIsoWithOffset(String(form.get("scheduled_at"))),
          appointment_type: "follow_up",
          notes: String(form.get("notes") ?? "").trim() || null,
        }
      : {};

    try {
      await api.post(`/follow-ups/${followUp!.id}/complete`, payload);
      onDone(scheduleNext);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(error.fieldErrors);
        if (!Object.keys(error.fieldErrors).length) setMessage(error.message);
      } else {
        setMessage("Something went wrong. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open onClose={onCancel} title="Complete follow-up">
      <form onSubmit={handleSubmit} className="space-y-4">
        {message && (
          <div
            role="alert"
            className="rounded-md border border-brick/25 bg-brick-soft px-3 py-2 text-sm text-brick"
          >
            {message}
          </div>
        )}

        <div>
          <p className="font-medium text-ink">
            {followUp.patient?.full_name ?? "Patient"}
          </p>
          <p className="mt-0.5 text-ink-muted">{followUp.reason}</p>
        </div>

        <label className="flex items-start gap-2.5 rounded-md border border-hairline bg-ground p-3">
          <input
            type="checkbox"
            checked={scheduleNext}
            onChange={(event) => setScheduleNext(event.target.checked)}
            className="mt-0.5 h-4 w-4 accent-[--color-accent]"
          />
          <span>
            <span className="font-medium text-ink">
              Book the next appointment
            </span>
            <span className="block text-sm text-ink-muted">
              Checked by default — this is usually why the follow-up existed.
            </span>
          </span>
        </label>

        {scheduleNext && (
          <>
            <Field label="Date and time" error={errors.scheduled_at} required>
              {(props) => (
                <input
                  {...props}
                  name="scheduled_at"
                  type="datetime-local"
                  required
                  defaultValue={defaultSlot()}
                />
              )}
            </Field>

            <Field label="Notes" error={errors.notes}>
              {(props) => (
                <textarea
                  {...props}
                  name="notes"
                  rows={2}
                  maxLength={1000}
                  defaultValue={followUp.reason}
                  className={`${props.className} h-auto py-2`}
                />
              )}
            </Field>
          </>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" onClick={onCancel} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={saving}>
            {scheduleNext ? "Complete and book" : "Mark complete"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
