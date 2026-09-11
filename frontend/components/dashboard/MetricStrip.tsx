import { AlertCircle, CalendarClock, CalendarDays, Users } from "lucide-react";

import { cx } from "@/lib/utils";
import type { DashboardMetrics } from "@/types/api";

interface Metric {
  label: string;
  value: number;
  icon: typeof Users;
  urgent?: boolean;
}

export function MetricStrip({ metrics }: { metrics: DashboardMetrics }) {
  const items: Metric[] = [
    { label: "Patients", value: metrics.total_patients, icon: Users },
    { label: "Today", value: metrics.appointments_today, icon: CalendarDays },
    {
      label: "Upcoming",
      value: metrics.upcoming_appointments,
      icon: CalendarClock,
    },
    {
      label: "Needs attention",
      value: metrics.follow_ups_needing_attention,
      icon: AlertCircle,
      urgent: metrics.follow_ups_needing_attention > 0,
    },
  ];

  return (
    <dl className="grid grid-cols-2 divide-x divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface sm:grid-cols-4 sm:divide-y-0">
      {items.map(({ label, value, icon: Icon, urgent }) => (
        <div key={label} className="flex items-start gap-3 px-4 py-3.5">
          <span
            aria-hidden="true"
            className={cx(
              "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
              urgent ? "bg-brick-soft text-brick" : "bg-ground text-ink-muted",
            )}
          >
            <Icon className="h-4 w-4" />
          </span>

          <div className="min-w-0">
            <dt className="truncate text-sm text-ink-muted">{label}</dt>
            <dd
              className={cx(
                "mt-0.5 text-2xl font-semibold tabular leading-none",
                urgent ? "text-brick" : "text-ink",
              )}
            >
              {value}
            </dd>
          </div>
        </div>
      ))}
    </dl>
  );
}

export function MetricStripSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="grid grid-cols-2 divide-x divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface sm:grid-cols-4 sm:divide-y-0"
    >
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="flex items-start gap-3 px-4 py-3.5">
          <div className="h-8 w-8 shrink-0 animate-pulse rounded-md bg-ground" />
          <div className="min-w-0 flex-1">
            <div className="h-4 w-20 animate-pulse rounded-sm bg-ground" />
            <div className="mt-1.5 h-6 w-10 animate-pulse rounded-sm bg-ground" />
          </div>
        </div>
      ))}
    </div>
  );
}
