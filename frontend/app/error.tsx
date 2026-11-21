"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { ButtonLink, StatusScreen } from "@/components/ui/StatusScreen";

/**
 * Root error boundary. Catches render errors on the landing and auth pages,
 * and anything thrown by the app shell's own layout (which the in-app
 * boundary in app/(app)/error.tsx sits below and cannot catch).
 *
 * In production, errors from Server Components arrive with a generic
 * message and a `digest` — never the original message — so nothing
 * sensitive reaches the browser. The digest is shown so a user can quote it
 * and it can be matched against the server logs.
 */
export default function RootError({
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
      title="Something went wrong"
      description={
        <>
          <p>
            This page hit an unexpected problem. Trying again usually fixes
            it. If the server has been idle, it can take up to a minute to
            wake up.
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
      <ButtonLink href="/">Back to home</ButtonLink>
    </StatusScreen>
  );
}
