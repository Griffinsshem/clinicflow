import { LogoMark } from "@/components/Logo";

/**
 * Root loading state. Its main job is the first load into the app: the
 * shell layout verifies the session with the API before anything renders,
 * and on the free tier a sleeping server takes 30–60 seconds to answer.
 * Without this, that wait is a blank page.
 *
 * The cold-start hint is revealed by a CSS animation delay rather than a
 * JavaScript timer. This screen is the first thing streamed to a new
 * visitor, often before any JavaScript has loaded, so a timer would start
 * late or not at all. The delay matches the demo button's 5 seconds.
 */
export default function RootLoading() {
  return (
    <main
      className="flex min-h-dvh flex-col items-center justify-center px-4 text-center"
      aria-busy="true"
    >
      <LogoMark className="h-9 w-9 animate-pulse text-accent" />
      <p role="status" className="mt-4 text-base font-medium text-ink">
        Loading ClinicFlow…
      </p>
      <p className="mt-1 min-h-10 max-w-xs text-sm text-ink-muted [animation:rise-in_380ms_cubic-bezier(0.2,0.6,0.2,1)_5s_both]">
        The server is waking up. This can take up to a minute the first time.
      </p>
    </main>
  );
}
