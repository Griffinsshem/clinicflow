"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { ApiError, api } from "@/lib/client";
import type { FollowUp, Patient } from "@/types/api";

function defaultDate(): string {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  return date.toISOString().slice(0, 10);
}

export function FollowUpForm({
  patient,
  onSaved,
  onCancel,
}: {
  patient: Patient;
  onSaved: (followUp: FollowUp) => void;
  onCancel: () => void;
}) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage(null);

    const form = new FormData(event.currentTarget);

    try {
      const result = await api.post<FollowUp>("/follow-ups", {
        patient_id: patient.id,
        follow_up_date: form.get("follow_up_date"),
        reason: String(form.get("reason") ?? "").trim(),
      });
      onSaved(result.data);
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
        <p className="text-sm font-medium text-ink">Patient</p>
        <p className="mt-1 text-ink-muted">{patient.full_name}</p>
      </div>

      <Field label="Follow up by" error={errors.follow_up_date} required>
        {(props) => (
          <input
            {...props}
            name="follow_up_date"
            type="date"
            required
            defaultValue={defaultDate()}
          />
        )}
      </Field>

      <Field
        label="Reason"
        error={errors.reason}
        hint="What needs checking when they come back."
        required
      >
        {(props) => (
          <input
            {...props}
            name="reason"
            required
            minLength={3}
            maxLength={500}
            placeholder="Review blood pressure readings"
          />
        )}
      </Field>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" loading={saving}>
          Add follow-up
        </Button>
      </div>
    </form>
  );
}
