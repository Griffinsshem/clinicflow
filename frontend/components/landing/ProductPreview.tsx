import { AlertCircle, CalendarClock, CalendarDays, Users } from "lucide-react";

import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";


const METRICS = [
  { label: "Patients", value: "142", icon: Users },
  { label: "Today", value: "8", icon: CalendarDays },
  { label: "Upcoming", value: "31", icon: CalendarClock },
  { label: "Needs attention", value: "5", icon: AlertCircle, urgent: true },
] as const;

const SCHEDULE = [
  { time: "9:00 AM", name: "Mercy Wambui", type: "Check-up", status: "Confirmed" },
  { time: "10:30 AM", name: "Joseph Otieno", type: "Consultation", status: "Confirmed" },
  { time: "1:00 PM", name: "Grace Akinyi", type: "Follow-up", status: "Scheduled" },
] as const;

const ATTENTION = [
  { name: "Esther Odhiambo", reason: "Check on medication side effects", when: "9 days ago", overdue: true },
  { name: "Naomi Kamau", reason: "Repeat prescription review", when: "5 days ago", overdue: true },
  { name: "Faith Njoroge", reason: "Check wound healing", when: "Due today", overdue: false },
] as const;

export function ProductPreview() {
  return (
    <div
      aria-hidden="true"
      className="animate-rise overflow-hidden rounded-lg border border-line bg-surface shadow-[--shadow-overlay]"
    >
      <div className="flex items-center gap-2 border-b border-hairline bg-ground px-3 py-2.5">
        <div className="flex gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
        </div>
        <div className="mx-auto rounded-sm bg-surface px-3 py-0.5 text-xs text-ink-subtle">
          clinicflow.app/dashboard
        </div>
      </div>

      <div className="space-y-3 p-3 sm:p-4">
        <dl className="grid grid-cols-2 divide-x divide-y divide-hairline overflow-hidden rounded-md border border-hairline sm:grid-cols-4 sm:divide-y-0">
          {METRICS.map(({ label, value, icon: Icon, ...rest }) => {
            const urgent = "urgent" in rest;
            return (
              <div key={label} className="flex items-start gap-2 px-2.5 py-2">
                <span
                  className={
                    "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-sm " +
                    (urgent ? "bg-brick-soft text-brick" : "bg-ground text-ink-muted")
                  }
                >
                  <Icon className="h-3 w-3" />
                </span>
                <div className="min-w-0">
                  <dt className="truncate text-[0.6875rem] text-ink-muted">{label}</dt>
                  <dd
                    className={
                      "text-base font-semibold tabular leading-tight " +
                      (urgent ? "text-brick" : "text-ink")
                    }
                  >
                    {value}
                  </dd>
                </div>
              </div>
            );
          })}
        </dl>

        <div className="grid gap-3 sm:grid-cols-2">
          <PreviewPanel title="Today">
            {SCHEDULE.map((row) => (
              <div key={row.name} className="flex items-center gap-2 px-2.5 py-2">
                <span
                  className="w-14 shrink-0 text-[0.6875rem] font-medium tabular text-ink"
                >
                  {row.time}
                </span>
                <Avatar name={row.name} size="sm" className="h-5 w-5 text-[0.625rem]" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-ink">{row.name}</p>
                  <p className="truncate text-[0.6875rem] text-ink-muted">{row.type}</p>
                </div>
              </div>
            ))}
          </PreviewPanel>

          <PreviewPanel title="Needs attention">
            {ATTENTION.map((row) => (
              <div key={row.reason} className="flex items-start gap-2 px-2.5 py-2">
                <Avatar name={row.name} size="sm" className="h-5 w-5 text-[0.625rem]" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-ink">{row.name}</p>
                  <p className="truncate text-[0.6875rem] text-ink-muted">{row.reason}</p>
                </div>
                <Badge
                  tone={row.overdue ? "brick" : "ochre"}
                  className="shrink-0 px-1 py-0 text-[0.625rem]"
                >
                  {row.overdue ? "Overdue" : "Due today"}
                </Badge>
              </div>
            ))}
          </PreviewPanel>
        </div>
      </div>
    </div>
  );
}

function PreviewPanel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-md border border-hairline">
      <p className="border-b border-hairline px-2.5 py-1.5 text-xs font-semibold text-ink">
        {title}
      </p>
      <div className="divide-y divide-hairline">{children}</div>
    </div>
  );
}
