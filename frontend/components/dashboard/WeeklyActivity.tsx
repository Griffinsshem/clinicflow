import { Panel, PanelHeader } from "@/components/ui/Panel";
import { formatWeekday } from "@/lib/format";


interface Day {
  date: string;
  count: number;
}

export function WeeklyActivity({ days }: { days: Day[] }) {
  const peak = Math.max(1, ...days.map((day) => day.count));

  return (
    <Panel>
      <PanelHeader title="Last seven days" />

      <div className="px-4 py-4">
        <div
          className="flex gap-2"
          role="img"
          aria-label={`Appointments per day: ${days
            .map((day) => `${formatWeekday(day.date)} ${day.count}`)
            .join(", ")}`}
        >
          {days.map((day) => (
            <div key={day.date} className="flex-1">
              <div className="relative h-24 rounded-sm bg-ground">
                <div
                  className="absolute inset-x-0 bottom-0 rounded-sm bg-accent/15 border-t-2 border-accent"
                  style={{
                    height: day.count === 0 ? "2px" : `${(day.count / peak) * 100}%`,
                  }}
                />
                {day.count > 0 && (
                  <span className="absolute inset-x-0 top-1 text-center text-xs font-medium tabular text-ink-muted">
                    {day.count}
                  </span>
                )}
              </div>
              <p className="mt-1.5 text-center text-xs text-ink-subtle">
                {formatWeekday(day.date)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
