import Link from "next/link";

import { AppointmentBadge } from "@/components/ui/Badge";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { EmptyState } from "@/components/ui/States";
import { formatTime, humanise } from "@/lib/format";
import type { Appointment } from "@/types/api";

export function TodaySchedule({ appointments }: { appointments: Appointment[] }) {
  return (
    <Panel>
      <PanelHeader
        title="Today"
        action={
          <Link
            href="/appointments"
            className="text-sm font-bold text-accent hover:underline"
          >
            All appointments
          </Link>
        }
      />

      {appointments.length === 0 ? (
        <EmptyState
          title="Nothing scheduled today"
          description="Appointments booked for today will appear here in time order."
        />
      ) : (
        <ul className="divide-y divide-hairline">
          {appointments.map((appointment) => (
            <li key={appointment.id}>
              <Link
                href={`/patients/${appointment.patient_id}`}
                className="flex items-center gap-4 px-4 py-3 hover:bg-ground transition-colors duration-150"
              >
                <time
                  dateTime={appointment.scheduled_at}
                  className="w-16 shrink-0 text-sm font-medium tabular text-ink"
                >
                  {formatTime(appointment.scheduled_at)}
                </time>

                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-ink">
                    {appointment.patient?.full_name ?? "Unknown patient"}
                  </p>
                  <p className="text-sm text-ink-muted">
                    {humanise(appointment.appointment_type)}
                  </p>
                </div>

                <AppointmentBadge status={appointment.status} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
