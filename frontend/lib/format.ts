
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
