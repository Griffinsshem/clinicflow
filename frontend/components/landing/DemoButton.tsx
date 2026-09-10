"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { timezoneOffsetMinutes } from "@/lib/client";


export function DemoButton({
  size = "md",
  variant = "primary",
}: {
  size?: "sm" | "md";
  variant?: "primary" | "secondary";
}) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "working" | "error">("idle");

  async function startDemo() {
    setState("working");
    try {
      const response = await fetch(
        `/api/demo?tz_offset=${timezoneOffsetMinutes()}`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error();
      router.refresh();
      router.push("/dashboard");
    } catch {
      setState("error");
    }
  }

  if (state === "error") {
    return (
      <div className="text-sm">
        <p className="text-brick">Couldn&apos;t start the demo.</p>
        <button
          onClick={startDemo}
          className="mt-0.5 font-medium text-accent hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <Button
      variant={variant}
      size={size}
      loading={state === "working"}
      onClick={startDemo}
    >
      {state === "working" ? "Setting up your clinic…" : "Explore the demo"}
    </Button>
  );
}
