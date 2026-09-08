
const TIME = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
});

const DATE = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const WEEKDAY = new Intl.DateTimeFormat(undefined, { weekday: "short" });

export function formatTime(iso: string): string {
  return TIME.format(new Date(iso));
}

export function formatDate(iso: string): string {
  if (iso.length === 10) {
    const [year, month, day] = iso.split("-").map(Number);
    return DATE.format(new Date(year, month - 1, day));
  }
  return DATE.format(new Date(iso));
}

export function formatWeekday(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return WEEKDAY.format(new Date(year, month - 1, day));
}

const RELATIVE = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

export function relativeDays(isoDate: string, today = new Date()): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const target = new Date(year, month - 1, day);
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());

  const days = Math.round((target.getTime() - start.getTime()) / 86_400_000);
  return RELATIVE.format(days, "day");
}

export function humanise(value: string): string {
  const spaced = value.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

const DAY_HEADING = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  day: "numeric",
  month: "short",
});

export function dayHeading(iso: string, today = new Date()): string {
  const date = new Date(iso);

  const startOfDay = (d: Date) =>
    new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

  const days = Math.round(
    (startOfDay(date) - startOfDay(today)) / 86_400_000,
  );

  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  if (days === -1) return "Yesterday";
  return DAY_HEADING.format(date);
}

export function groupByDay<T>(
  items: T[],
  getDate: (item: T) => string,
): { key: string; label: string; items: T[] }[] {
  const groups = new Map<string, T[]>();

  for (const item of items) {
    const date = new Date(getDate(item));
    const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
    const bucket = groups.get(key);
    if (bucket) bucket.push(item);
    else groups.set(key, [item]);
  }

  return Array.from(groups.entries()).map(([key, groupItems]) => ({
    key,
    label: dayHeading(getDate(groupItems[0])),
    items: groupItems,
  }));
}
