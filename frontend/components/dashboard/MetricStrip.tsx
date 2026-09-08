import { cx } from "@/lib/utils";
import type { DashboardMetrics } from "@/types/api";


interface Metric {
  label: string;
  value: number;
  urgent?: boolean;
}

export function MetricStrip({ metrics }: { metrics: DashboardMetrics }) {
  const items: Metric[] = [
    { label: "Patients", value: metrics.total_patients },
    { label: "Today", value: metrics.appointments_today },
    { label: "Upcoming", value: metrics.upcoming_appointments },
    {
      label: "Needs attention",
      value: metrics.follow_ups_needing_attention,
      urgent: metrics.follow_ups_needing_attention > 0,
    },
  ];

  return (
    <dl
      className={
        "grid grid-cols-2 sm:grid-cols-4 " +
        "bg-surface border border-hairline rounded-lg overflow-hidden " +
        "divide-x divide-y sm:divide-y-0 divide-hairline"
      }
    >
      {items.map(({ label, value, urgent }) => (
        <div key={label} className="px-4 py-3.5">
          <dt className="text-sm text-ink-muted">{label}</dt>
          <dd
            className={cx(
              "mt-0.5 text-2xl font-semibold tabular",
              urgent ? "text-brick" : "text-ink",
            )}
          >
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function MetricStripSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="grid grid-cols-2 sm:grid-cols-4 bg-surface border border-hairline rounded-lg overflow-hidden divide-x divide-y sm:divide-y-0 divide-hairline"
    >
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="px-4 py-3.5">
          <div className="h-4 w-20 rounded-sm bg-ground animate-pulse" />
          <div className="mt-1.5 h-7 w-10 rounded-sm bg-ground animate-pulse" />
        </div>
      ))}
    </div>
  );
}
