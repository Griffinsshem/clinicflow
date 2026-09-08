import { cx } from "@/lib/utils";

import type { AppointmentStatus } from "@/types/api";
import { humanise } from "@/lib/format";


type Tone = "neutral" | "accent" | "ochre" | "brick" | "quiet";

const TONES: Record<Tone, string> = {
  neutral: "bg-ground text-ink-muted border-hairline",
  accent: "bg-accent-soft text-accent border-accent/20",
  ochre: "bg-ochre-soft text-ochre border-ochre/25",
  brick: "bg-brick-soft text-brick border-brick/25",
  quiet: "bg-transparent text-ink-subtle border-hairline",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 " +
          "text-xs font-medium whitespace-nowrap",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

const APPOINTMENT_TONES: Record<AppointmentStatus, Tone> = {
  scheduled: "neutral",
  confirmed: "accent",
  completed: "quiet",   
  cancelled: "quiet",
  no_show: "brick",     
};

export function AppointmentBadge({ status }: { status: AppointmentStatus }) {
  return <Badge tone={APPOINTMENT_TONES[status]}>{humanise(status)}</Badge>;
}
