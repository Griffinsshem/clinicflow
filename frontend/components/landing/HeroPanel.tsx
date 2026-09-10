import { Badge } from "@/components/ui/Badge";


const ROWS = [
  { name: "Esther Odhiambo", reason: "Check on medication side effects", overdue: "9 days ago" },
  { name: "Naomi Kamau", reason: "Repeat prescription review", overdue: "5 days ago" },
  { name: "Joseph Kamau", reason: "Review blood pressure readings", overdue: "2 days ago" },
  { name: "Faith Njoroge", reason: "Check wound healing", due: true },
] as const;

const STAGGER_MS = 70;

export function HeroPanel() {
  return (
    <div
      aria-hidden="true"
      className="animate-rise rounded-lg border border-hairline bg-surface"
    >
      <header className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <h3 className="text-base font-semibold text-ink">Needs attention</h3>
        <span className="text-sm text-ink-muted tabular">{ROWS.length}</span>
      </header>

      <ul className="divide-y divide-hairline">
        {ROWS.map((row, index) => (
          <li
            key={row.name}
            className="animate-rise flex items-start justify-between gap-3 px-4 py-3"
            style={{ animationDelay: `${120 + index * STAGGER_MS}ms` }}
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-ink">{row.name}</p>
              <p className="truncate text-sm text-ink-muted">{row.reason}</p>
            </div>
            <div className="shrink-0 text-right">
              <Badge tone={"due" in row ? "ochre" : "brick"}>
                {"due" in row ? "Due today" : "Overdue"}
              </Badge>
              {"overdue" in row && (
                <p className="mt-1 text-xs text-ink-subtle">{row.overdue}</p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
