import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ButtonLink, StatusScreen } from "@/components/ui/StatusScreen";
import { SESSION_COOKIE } from "@/lib/session";

export const metadata: Metadata = {
  title: "Page not found · ClinicFlow",
};

/**
 * Root not-found: renders for every URL the app doesn't match, and for any
 * notFound() call that no closer not-found.tsx handles.
 *
 * Signed-in staff are sent back to their dashboard; everyone else to the
 * landing page. Only the cookie's presence is checked — this page shows
 * no clinic data, so there is nothing to verify against the backend.
 */
export default async function NotFound() {
  const cookieStore = await cookies();
  const signedIn = cookieStore.has(SESSION_COOKIE);

  return (
    <StatusScreen
      eyebrow="404"
      title="We couldn't find that page"
      description={
        <p>
          The link may be mistyped, or the page may have moved.
        </p>
      }
    >
      {signedIn ? (
        <>
          <ButtonLink href="/dashboard" variant="primary">
            Go to dashboard
          </ButtonLink>
          <ButtonLink href="/patients">Find a patient</ButtonLink>
        </>
      ) : (
        <>
          <ButtonLink href="/" variant="primary">
            Back to home
          </ButtonLink>
          <ButtonLink href="/login">Sign in</ButtonLink>
        </>
      )}
    </StatusScreen>
  );
}
