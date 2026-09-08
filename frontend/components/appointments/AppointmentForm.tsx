"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { ApiError, api } from "@/lib/client";
import type { Appointment, Patient } from "@/types/api";


interface AppointmentFormProps {
  appointment?: Appointment;
  patient?: Patient;
  patients?: Patient[];
  onSaved: (appointment: Appointment) => void;
  onCancel: () => void;
}

function toLocalInputValue(iso?: string): string {
  const date = iso ? new Date(iso) : nextSensibleSlot();
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

function nextSensibleSlot(): Date {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  date.setHours(9, 0, 0, 0);
  return date;
}

function toIsoWithOffset(localValue: string): string {
  const date = new Date(localValue);
  const offsetMinutes = -date.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const pad = (n: number) => String(Math.floor(Math.abs(n))).padStart(2, "0");
  return `${localValue}:00${sign}${pad(offsetMinutes / 60)}:${pad(offsetMinutes % 60)}`;
}

export function AppointmentForm({
  appointment,
  patient,
  patients,
  onSaved,
  onCancel,
}: AppointmentFormProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const isEdit = Boolean(appointment);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage(null);

    const form = new FormData(event.currentTarget);
    const scheduledAt = toIsoWithOffset(String(form.get("scheduled_at")));

    try {
      let result;
      if (appointment) {
        result = await api.patch<Appointment>(`/appointments/${appointment.id}`, {
          scheduled_at: scheduledAt,
          appointment_type: form.get("appointment_type"),
          notes: String(form.get("notes") ?? "").trim() || null,
        });
      } else {
        result = await api.post<Appointment>("/appointments", {
          patient_id: Number(patient?.id ?? form.get("patient_id")),
          scheduled_at: scheduledAt,
          appointment_type: form.get("appointment_type"),
          notes: String(form.get("notes") ?? "").trim() || null,
        });
      }
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

      {patient ? (
        <div>
          <p className="text-sm font-medium text-ink">Patient</p>
          <p className="mt-1 text-ink-muted">{patient.full_name}</p>
        </div>
      ) : !isEdit && patients ? (
        <Field label="Patient" error={errors.patient_id} required>
          {(props) => (
            <select {...props} name="patient_id" required defaultValue="">
              <option value="" disabled>
                Choose a patient
              </option>
              {patients.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.full_name}
                </option>
              ))}
            </select>
          )}
        </Field>
      ) : null}

      <Field label="Date and time" error={errors.scheduled_at} required>
        {(props) => (
          <input
            {...props}
            name="scheduled_at"
            type="datetime-local"
            required
            defaultValue={toLocalInputValue(appointment?.scheduled_at)}
          />
        )}
      </Field>

      <Field label="Type" error={errors.appointment_type}>
        {(props) => (
          <select
            {...props}
            name="appointment_type"
            defaultValue={appointment?.appointment_type ?? "consultation"}
          >
            <option value="consultation">Consultation</option>
            <option value="check_up">Check-up</option>
            <option value="follow_up">Follow-up</option>
            <option value="other">Other</option>
          </select>
        )}
      </Field>

      <Field label="Notes" error={errors.notes}>
        {(props) => (
          <textarea
            {...props}
            name="notes"
            rows={3}
            maxLength={1000}
            defaultValue={appointment?.notes ?? ""}
            className={`${props.className} h-auto py-2`}
          />
        )}
      </Field>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" loading={saving}>
          {isEdit ? "Save changes" : "Schedule"}
        </Button>
      </div>
    </form>
  );
}
