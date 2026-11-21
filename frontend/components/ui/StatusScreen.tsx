import Link from "next/link";

import { Logo } from "@/components/Logo";
import { cx } from "@/lib/utils";

/**
 * Shared layout for the app's system screens: not found, errors, and the
 * full-page loader. Two placements:
 *
 *  - "page":  a standalone screen with the logo, used outside the app shell
 *             (unknown URLs, landing and auth errors, the first load).
 *  - "panel": sits inside the app shell's content area, so the navigation
 *             stays usable and the user is never stranded.
 */
export function StatusScreen({
  placement = "page",
  eyebrow,
  title,
  description,
  children,
}: {
  placement?: "page" | "panel";
  eyebrow?: string;
  title: string;
  description: React.ReactNode;
  children?: React.ReactNode;
}) {
  const body = (
    <div className="animate-rise">
      {eyebrow && (
        <p className="text-sm font-medium tabular text-ink-subtle">{eyebrow}</p>
      )}
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">
        {title}
      </h1>
      <div className="mt-2 text-base text-ink-muted">{description}</div>
      {children && (
        <div className="mt-6 flex flex-wrap items-center gap-3">{children}</div>
      )}
    </div>
  );

  if (placement === "panel") {
    return (
      <section className="rounded-lg border border-hairline bg-surface px-6 py-12 md:px-10">
        <div className="max-w-md">{body}</div>
      </section>
    );
  }

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <Link href="/" aria-label="ClinicFlow home">
            <Logo className="text-lg" />
          </Link>
        </div>
        {body}
      </div>
    </main>
  );
}

const LINK_BASE =
  "inline-flex h-9 items-center justify-center gap-2 rounded-md px-4 " +
  "text-base font-medium transition-colors duration-150";

const LINK_VARIANTS = {
  primary: "bg-accent text-white hover:bg-accent-hover",
  secondary:
    "border border-line bg-surface text-ink hover:border-ink-subtle hover:bg-ground",
} as const;

/** A navigation link styled to match <Button>. */
export function ButtonLink({
  href,
  variant = "secondary",
  children,
}: {
  href: string;
  variant?: keyof typeof LINK_VARIANTS;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} className={cx(LINK_BASE, LINK_VARIANTS[variant])}>
      {children}
    </Link>
  );
}
