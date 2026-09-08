"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarDays,
  LayoutDashboard,
  RotateCcw,
  Users,
} from "lucide-react";

import { cx } from "@/lib/utils";


const ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/patients", label: "Patients", icon: Users },
  { href: "/appointments", label: "Appointments", icon: CalendarDays },
  { href: "/follow-ups", label: "Follow-ups", icon: RotateCcw },
] as const;

export function Nav() {
  const pathname = usePathname();

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <>
      {/* Desktop rail */}
      <nav
        aria-label="Main"
        className="hidden md:flex md:w-56 md:flex-col md:shrink-0 border-r border-hairline bg-surface"
      >
        <div className="px-5 h-14 flex items-center border-b border-hairline">
          <Link href="/dashboard" className="font-semibold tracking-tight text-ink">
            ClinicFlow
          </Link>
        </div>

        <ul className="flex-1 p-2 space-y-0.5">
          {ITEMS.map(({ href, label, icon: Icon }) => (
            <li key={href}>
              <Link
                href={href}
                aria-current={isActive(href) ? "page" : undefined}
                className={cx(
                  "flex items-center gap-2.5 rounded-[--radius-md] px-3 py-2 " +
                    "text-sm transition-colors duration-150",
                  isActive(href)
                    ? "bg-accent-soft text-accent font-medium"
                    : "text-ink-muted hover:bg-ground hover:text-ink",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Mobile bottom bar */}
      <nav
        aria-label="Main"
        className="md:hidden fixed inset-x-0 bottom-0 z-20 border-t border-hairline bg-surface"
      >
        <ul className="grid grid-cols-4">
          {ITEMS.map(({ href, label, icon: Icon }) => (
            <li key={href}>
              <Link
                href={href}
                aria-current={isActive(href) ? "page" : undefined}
                className={cx(
                  "flex h-14 flex-col items-center justify-center gap-0.5 text-xs",
                  isActive(href) ? "text-accent font-medium" : "text-ink-muted",
                )}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
