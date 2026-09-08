"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Field, controlClass } from "@/components/ui/Field";
import { ApiError, api } from "@/lib/client";
import type { Patient } from "@/types/api";


interface PatientFormProps {
  patient?: Patient;
  onSaved: (patient: Patient) => void;
  onCancel: () => void;
}

export function PatientForm({ patient, onSaved, onCancel }: PatientFormProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      full_name: String(form.get("full_name") ?? "").trim(),
      date_of_birth: form.get("date_of_birth") || null,
      gender: form.get("gender") || null,
      phone: String(form.get("phone") ?? "").trim() || null,
      email: String(form.get("email") ?? "").trim() || null,
    };

    try {
      const result = patient
        ? await api.patch<Patient>(`/patients/${patient.id}`, payload)
        : await api.post<Patient>("/patients", payload);
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

      <Field label="Full name" error={errors.full_name} required>
        {(props) => (
          <input
            {...props}
            name="full_name"
            defaultValue={patient?.full_name}
            required
            minLength={2}
            maxLength={120}
            autoFocus
          />
        )}
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Date of birth" error={errors.date_of_birth}>
          {(props) => (
            <input
              {...props}
              name="date_of_birth"
              type="date"
              defaultValue={patient?.date_of_birth ?? ""}
              max={new Date().toISOString().slice(0, 10)}
            />
          )}
        </Field>

        <Field label="Gender" error={errors.gender}>
          {(props) => (
            <select {...props} name="gender" defaultValue={patient?.gender ?? ""}>
              <option value="">Not recorded</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
              <option value="undisclosed">Prefer not to say</option>
            </select>
          )}
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Phone" error={errors.phone}>
          {(props) => (
            <input
              {...props}
              name="phone"
              type="tel"
              defaultValue={patient?.phone ?? ""}
              maxLength={32}
            />
          )}
        </Field>

        <Field label="Email" error={errors.email}>
          {(props) => (
            <input
              {...props}
              name="email"
              type="email"
              defaultValue={patient?.email ?? ""}
            />
          )}
        </Field>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" loading={saving}>
          {patient ? "Save changes" : "Add patient"}
        </Button>
      </div>
    </form>
  );
}

export { controlClass };
