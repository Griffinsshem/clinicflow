"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useCallback, useState } from "react";
import { ArrowLeft, CalendarPlus, Pencil, Plus, Trash2 } from "lucide-react";

import { AppointmentForm } from "@/components/appointments/AppointmentForm";
import { StatusMenu } from "@/components/appointments/StatusMenu";
import { FollowUpForm } from "@/components/follow-ups/FollowUpForm";
import { PatientForm } from "@/components/patients/PatientForm";
import { AppointmentBadge, Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Modal } from "@/components/ui/Modal";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { ApiError, api, timezoneOffsetMinutes } from "@/lib/client";
import { formatDate, formatTime, humanise, relativeDays } from "@/lib/format";
import { useToast } from "@/providers/ToastProvider";
import type { Appointment, FollowUp, Patient } from "@/types/api";

type Dialog = "edit" | "schedule" | "follow-up" | "delete" | null;

export default function PatientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const toast = useToast();

  const [dialog, setDialog] = useState<Dialog>(null);

  const patientState = useApi<Patient>(`/patients/${id}`);
  const appointmentsState = useApi<Appointment[]>(`/patients/${id}/appointments`);
  const followUpsState = useApi<FollowUp[]>(
    `/patients/${id}/follow-ups?tz_offset=${timezoneOffsetMinutes()}`,
  );

  const refetchAll = useCallback(() => {
    void patientState.refetch();
    void appointmentsState.refetch();
    void followUpsState.refetch();
  }, [patientState, appointmentsState, followUpsState]);

  async function deletePatient() {
    try {
      await api.delete(`/patients/${id}`);
      toast("Patient removed.");
      router.push("/patients");
    } catch (error) {
      toast(
        error instanceof ApiError ? error.message : "Couldn't remove the patient.",
        "error",
      );
    }
  }

  if (patientState.error) {
    return (
      <Panel>
        <ErrorState message={patientState.error} onRetry={patientState.refetch} />
      </Panel>
    );
  }

  const patient = patientState.data;
  const now = Date.now();
  const appointments = appointmentsState.data ?? [];
  const upcoming = appointments
    .filter((a) => new Date(a.scheduled_at).getTime() >= now)
    .reverse();
  const past = appointments.filter((a) => new Date(a.scheduled_at).getTime() < now);

  const followUps = followUpsState.data ?? [];
  const openFollowUps = followUps.filter((f) => f.status === "upcoming");

  return (
    <div className="space-y-5">
      <Link
        href="/patients"
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted transition-colors hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        All patients
      </Link>

      {!patient ? (
        <Panel>
          <SkeletonRows rows={2} />
        </Panel>
      ) : (
        <>
          <PatientHeader
            patient={patient}
            onEdit={() => setDialog("edit")}
            onDelete={() => setDialog("delete")}
          />

          <Panel>
            <PanelHeader
              title="Follow-ups"
              action={
                <Button size="sm" onClick={() => setDialog("follow-up")}>
                  <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                  Add
                </Button>
              }
            />
            {followUpsState.loading ? (
              <SkeletonRows rows={2} />
            ) : openFollowUps.length === 0 ? (
              <EmptyState
                title="No open follow-ups"
                description="Add one when this patient needs seeing again by a certain date."
              />
            ) : (
              <ul className="divide-y divide-hairline">
                {openFollowUps.map((followUp) => (
                  <li
                    key={followUp.id}
                    className="flex items-start justify-between gap-3 px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="text-ink">{followUp.reason}</p>
                      <p className="mt-0.5 text-sm text-ink-muted">
                        Due {formatDate(followUp.follow_up_date)}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <Badge
                        tone={
                          followUp.is_overdue
                            ? "brick"
                            : followUp.is_due_today
                              ? "ochre"
                              : "neutral"
                        }
                      >
                        {followUp.is_overdue
                          ? "Overdue"
                          : followUp.is_due_today
                            ? "Due today"
                            : relativeDays(followUp.follow_up_date)}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel>
            <PanelHeader
              title="Upcoming appointments"
              action={
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setDialog("schedule")}
                >
                  <CalendarPlus className="h-3.5 w-3.5" aria-hidden="true" />
                  Schedule
                </Button>
              }
            />
            {appointmentsState.loading ? (
              <SkeletonRows rows={2} />
            ) : upcoming.length === 0 ? (
              <EmptyState
                title="Nothing booked"
                description="Schedule the next visit for this patient."
              />
            ) : (
              <ul className="divide-y divide-hairline">
                {upcoming.map((appointment) => (
                  <AppointmentRow
                    key={appointment.id}
                    appointment={appointment}
                    onChanged={refetchAll}
                    showActions
                  />
                ))}
              </ul>
            )}
          </Panel>

          <Panel>
            <PanelHeader title="History" />
            {appointmentsState.loading ? (
              <SkeletonRows rows={3} />
            ) : past.length === 0 ? (
              <EmptyState
                title="No past visits"
                description="Completed appointments will appear here."
              />
            ) : (
              <ul className="divide-y divide-hairline">
                {past.map((appointment) => (
                  <AppointmentRow
                    key={appointment.id}
                    appointment={appointment}
                    onChanged={refetchAll}
                  />
                ))}
              </ul>
            )}
          </Panel>

          <Modal
            open={dialog === "edit"}
            onClose={() => setDialog(null)}
            title="Edit patient"
          >
            <PatientForm
              patient={patient}
              onSaved={() => {
                setDialog(null);
                toast("Patient updated.");
                void patientState.refetch();
              }}
              onCancel={() => setDialog(null)}
            />
          </Modal>

          <Modal
            open={dialog === "schedule"}
            onClose={() => setDialog(null)}
            title="Schedule appointment"
          >
            <AppointmentForm
              patient={patient}
              onSaved={() => {
                setDialog(null);
                toast("Appointment scheduled.");
                void appointmentsState.refetch();
              }}
              onCancel={() => setDialog(null)}
            />
          </Modal>

          <Modal
            open={dialog === "follow-up"}
            onClose={() => setDialog(null)}
            title="Add follow-up"
          >
            <FollowUpForm
              patient={patient}
              onSaved={() => {
                setDialog(null);
                toast("Follow-up added.");
                void followUpsState.refetch();
              }}
              onCancel={() => setDialog(null)}
            />
          </Modal>

          <ConfirmDialog
            open={dialog === "delete"}
            title={`Remove ${patient.full_name}?`}
            description="Their appointments and follow-ups will be removed too. This can't be undone."
            confirmLabel="Remove patient"
            onConfirm={deletePatient}
            onCancel={() => setDialog(null)}
          />
        </>
      )}
    </div>
  );
}

function PatientHeader({
  patient,
  onEdit,
  onDelete,
}: {
  patient: Patient;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <Panel className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-ink">
            {patient.full_name}
          </h1>
          <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <div className="flex gap-1.5">
              <dt className="text-ink-subtle">Phone</dt>
              <dd className="text-ink tabular">{patient.phone ?? "—"}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-ink-subtle">Email</dt>
              <dd className="text-ink">{patient.email ?? "—"}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-ink-subtle">Born</dt>
              <dd className="text-ink tabular">
                {patient.date_of_birth ? formatDate(patient.date_of_birth) : "—"}
              </dd>
            </div>
            {patient.gender && (
              <div className="flex gap-1.5">
                <dt className="text-ink-subtle">Gender</dt>
                <dd className="text-ink">{humanise(patient.gender)}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="flex gap-2">
          <Button size="sm" onClick={onEdit}>
            <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
            Edit
          </Button>
          <Button size="sm" variant="danger" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            Remove
          </Button>
        </div>
      </div>
    </Panel>
  );
}

function AppointmentRow({
  appointment,
  onChanged,
  showActions = false,
}: {
  appointment: Appointment;
  onChanged: () => void;
  showActions?: boolean;
}) {
  return (
    <li className="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
      <div className="min-w-0">
        <p className="font-medium text-ink tabular">
          {formatDate(appointment.scheduled_at)} at{" "}
          {formatTime(appointment.scheduled_at)}
        </p>
        <p className="mt-0.5 text-sm text-ink-muted">
          {humanise(appointment.appointment_type)}
        </p>
        {appointment.notes && (
          <p className="mt-1 text-sm text-ink-muted">{appointment.notes}</p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {showActions && (
          <StatusMenu appointment={appointment} onChanged={onChanged} />
        )}
        <AppointmentBadge status={appointment.status} />
      </div>
    </li>
  );
}
