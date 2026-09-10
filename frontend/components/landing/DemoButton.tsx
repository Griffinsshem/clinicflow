"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { timezoneOffsetMinutes } from "@/lib/client";


const SLOW_THRESHOLD_MS = 5000;

type State = "idle" | "working" | "error";

export function DemoButton({
  size = "md",
  variant = "primary",
}: {
  size?: "sm" | "md";
  variant?: "primary" | "secondary";
}) {
  const router = useRouter();
  const [state, setState] = useState<State>("idle");
  const [slow, setSlow] = useState(false);
  const slowTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (slowTimer.current) window.clearTimeout(slowTimer.current);
    };
  }, []);

  async function startDemo() {
    setState("working");
    setSlow(false);
    slowTimer.current = window.setTimeout(
      () => setSlow(true),
      SLOW_THRESHOLD_MS,
    );

    try {
      const response = await fetch(
        `/api/demo?tz_offset=${timezoneOffsetMinutes()}`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error("demo request failed");
      router.refresh();
      router.push("/dashboard");
    } catch {
      setState("error");
    } finally {
      if (slowTimer.current) window.clearTimeout(slowTimer.current);
    }
  }

  return (
    <div className="space-y-2">
      <Button
        variant={variant}
        size={size}
        loading={state === "working"}
        onClick={startDemo}
      >
        {state === "working"
          ? "Setting up your clinic…"
          : state === "error"
            ? "Try again"
            : "Explore the demo"}
      </Button>

      {state === "working" && slow && (
        <p aria-live="polite" className="max-w-xs text-sm text-ink-muted">
          The demo server is waking up. This takes up to a minute the first
          time.
        </p>
      )}

      {state === "error" && (
        <p role="alert" className="max-w-xs text-sm text-brick">
          The demo server didn&apos;t respond. It may still be starting up —
          give it a moment and try again.
        </p>
      )}
    </div>
  );
}
