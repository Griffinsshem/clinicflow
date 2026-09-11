"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useMemo, useState } from "react";
import { CalendarPlus } from "lucide-react";

import { AppointmentForm } from "@/components/appointments/AppointmentForm";
import {
  FilterBar,
  type AppointmentFilters,
} from "@/components/appointments/FilterBar";
import { StatusMenu } from "@/components/appointments/StatusMenu";
import { Avatar } from "@/components/ui/Avatar";
import { AppointmentBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Pagination } from "@/components/ui/Pagination";
import { Panel } from "@/components/ui/Panel";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { formatTime, groupByDay, humanise } from "@/lib/format";
import { useToast } from "@/providers/ToastProvider";
import type { Appointment, Patient } from "@/types/api";


function startOfToday(): string {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function toIsoBoundary(date: string, endOfDay: boolean): string {
  const offsetMinutes = -new Date().getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const pad = (n: number) => String(Math.floor(Math.abs(n))).padStart(2, "0");
  const time = endOfDay ? "23:59:59" : "00:00:00";
  return `${date}T${time}${sign}${pad(offsetMinutes / 60)}:${pad(offsetMinutes % 60)}`;
}

export default function AppointmentsPage() {
  return (
    <Suspense fallback={null}>
      <AppointmentsView />
    </Suspense>
  );
}

function AppointmentsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  const [scheduling, setScheduling] = useState(false);

  const filters: AppointmentFilters = {
    date_from: searchParams.get("date_from") ?? startOfToday(),
    date_to: searchParams.get("date_to") ?? "",
    status: searchParams.get("status") ?? "",
    appointment_type: searchParams.get("appointment_type") ?? "",
  };

  const page = Number(searchParams.get("page") ?? 1);

  const updateQuery = useCallback(
    (changes: Record<string, string | number | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(changes)) {
        if (value === null || value === "") params.delete(key);
        else params.set(key, String(value));
      }
      if (!("page" in changes)) params.delete("page");
      router.replace(`/appointments?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const path = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.date_from) {
      params.set("date_from", toIsoBoundary(filters.date_from, false));
    }
    if (filters.date_to) {
      params.set("date_to", toIsoBoundary(filters.date_to, true));
    }
    if (filters.status) params.set("status", filters.status);
    if (filters.appointment_type) {
      params.set("appointment_type", filters.appointment_type);
    }
    if (page > 1) params.set("page", String(page));
    return `/appointments?${params.toString()}`;
  }, [filters, page]);

  const { data, meta, loading, error, refetch } = useApi<Appointment[]>(path);

  const patientsState = useApi<Patient[]>("/patients?limit=100");

  const groups = useMemo(
    () =>
      groupByDay(
        [...(data ?? [])].reverse(),
        (appointment) => appointment.scheduled_at,
      ),
    [data],
  );

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            Appointments
          </h1>
          <p className="mt-0.5 text-ink-muted tabular">
            {meta ? `${meta.total} in this view` : "\u00A0"}
          </p>
        </div>

        <Button variant="primary" onClick={() => setScheduling(true)}>
          <CalendarPlus className="h-4 w-4" aria-hidden="true" />
          Schedule
        </Button>
      </header>

      <FilterBar
        filters={filters}
        onChange={(changes) => updateQuery(changes)}
        onClear={() =>
          updateQuery({
            date_from: null,
            date_to: null,
            status: null,
            appointment_type: null,
          })
        }
      />

      {error ? (
        <Panel>
          <ErrorState message={error} onRetry={refetch} />
        </Panel>
      ) : loading ? (
        <Panel>
          <SkeletonRows rows={6} />
        </Panel>
      ) : !data?.length ? (
        <Panel>
          <EmptyState
            title="No appointments in this view"
            description="Adjust the filters, or schedule one."
            action={
              <Button variant="primary" onClick={() => setScheduling(true)}>
                Schedule appointment
              </Button>
            }
          />
        </Panel>
      ) : (
        <div className="space-y-4">
          {groups.map((group) => (
            <Panel key={group.key}>
              <h2 className="border-b border-hairline px-4 py-2.5 text-sm font-semibold text-ink">
                {group.label}
              </h2>

              <ul className="divide-y divide-hairline">
                {group.items.map((appointment) => (
                  <li
                    key={appointment.id}
                    className="px-4 py-3 sm:flex sm:items-center sm:gap-4"
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <time
                        dateTime={appointment.scheduled_at}
                        className="w-16 shrink-0 text-sm font-medium tabular text-ink"
                      >
                        {formatTime(appointment.scheduled_at)}
                      </time>

                      <Avatar
                        name={appointment.patient?.full_name ?? "?"}
                        size="sm"
                      />

                      <div className="min-w-0 flex-1">
                        <Link
                          href={`/patients/${appointment.patient_id}`}
                          className="block truncate font-medium text-ink hover:underline"
                        >
                          {appointment.patient?.full_name ?? "Unknown patient"}
                        </Link>
                        <p className="truncate text-sm text-ink-muted">
                          {humanise(appointment.appointment_type)}
                          {appointment.patient?.phone && (
                            <span className="tabular">
                              {" \u00B7 "}
                              {appointment.patient.phone}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="mt-2.5 flex items-center gap-2 pl-[6.25rem] sm:mt-0 sm:pl-0">
                      <StatusMenu
                        appointment={appointment}
                        onChanged={refetch}
                      />
                      <AppointmentBadge status={appointment.status} />
                    </div>
                  </li>
                ))}
              </ul>
            </Panel>
          ))}

          {meta && (
            <Panel>
              <Pagination
                meta={meta}
                onChange={(next) => updateQuery({ page: next })}
              />
            </Panel>
          )}
        </div>
      )}

      <Modal
        open={scheduling}
        onClose={() => setScheduling(false)}
        title="Schedule appointment"
      >
        <AppointmentForm
          patients={patientsState.data ?? []}
          onSaved={() => {
            setScheduling(false);
            toast("Appointment scheduled.");
            void refetch();
          }}
          onCancel={() => setScheduling(false)}
        />
      </Modal>
    </div>
  );
}
