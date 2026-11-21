"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { ButtonLink, StatusScreen } from "@/components/ui/StatusScreen";

/**
 * In-app error boundary. Renders inside the app shell, so the navigation
 * and user menu stay usable: a crash on one page never strands someone
 * mid-shift with no way to reach the rest of the clinic's records.
 *
 * Errors thrown by app/(app)/layout.tsx itself are above this boundary and
 * fall through to app/error.tsx.
 */
export default function AppError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <StatusScreen
      placement="panel"
      title="This page couldn't be shown"
      description={
        <>
          <p>
            Something unexpected went wrong while loading it. Nothing you
            saved earlier has been lost. Try again, or use the menu to carry
            on elsewhere.
          </p>
          {error.digest && (
            <p className="mt-3 text-sm text-ink-subtle">
              Reference: <span className="tabular">{error.digest}</span>
            </p>
          )}
        </>
      }
    >
      <Button variant="primary" onClick={() => retry()}>
        Try again
      </Button>
      <ButtonLink href="/dashboard">Go to dashboard</ButtonLink>
    </StatusScreen>
  );
}
