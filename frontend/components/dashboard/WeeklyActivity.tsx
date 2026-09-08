import { Panel, PanelHeader } from "@/components/ui/Panel";
import { formatWeekday } from "@/lib/format";


const CHART_HEIGHT = 88;
const LABEL_SPACE = 18;
const MAX_BAR = CHART_HEIGHT - LABEL_SPACE;

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
          className="flex items-end gap-2"
          role="img"
          aria-label={`Appointments per day: ${days
            .map((day) => `${formatWeekday(day.date)} ${day.count}`)
            .join(", ")}`}
        >
          {days.map((day) => {
            const barHeight =
              day.count === 0 ? 0 : Math.max(4, (day.count / peak) * MAX_BAR);

            return (
              <div key={day.date} className="flex-1">
                <div
                  className="flex flex-col justify-end"
                  style={{ height: CHART_HEIGHT }}
                >
                  {day.count > 0 && (
                    <span className="mb-1 text-center text-xs font-medium tabular text-ink-muted">
                      {day.count}
                    </span>
                  )}
                  <div
                    className="rounded-t-sm bg-accent/12"
                    style={{ height: barHeight }}
                  />
                </div>

                <div className="h-px bg-line" />

                <p className="mt-1.5 text-center text-xs text-ink-subtle">
                  {formatWeekday(day.date)}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </Panel>
  );
}
