"use client";

import { useEffect, useState } from "react";


function greetingFor(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

const DATE_FORMAT = new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  day: "numeric",
  month: "long",
});

export function Greeting({ name }: { name: string }) {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => setNow(new Date()), []);

  const firstName = name.trim().split(/\s+/)[0];

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        {now ? `${greetingFor(now.getHours())}, ${firstName}` : "\u00A0"}
      </h1>
      <p className="mt-0.5 text-ink-muted">
        {now ? DATE_FORMAT.format(now) : "\u00A0"}
      </p>
    </div>
  );
}
