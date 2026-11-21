import { Panel } from "@/components/ui/Panel";
import { SkeletonRows } from "@/components/ui/States";

/**
 * Shown inside the app shell while a page's segment loads. The navigation
 * stays put; only the content area is replaced, with the same heading +
 * panel shape every page in the app uses, so nothing jumps when it arrives.
 */
export default function AppLoading() {
  return (
    <div className="space-y-6" aria-busy="true">
      <span role="status" className="sr-only">
        Loading…
      </span>

      <div className="flex items-start justify-between gap-4" aria-hidden="true">
        <div className="space-y-2">
          <div className="h-6 w-44 rounded-sm bg-surface animate-pulse" />
          <div className="h-4 w-28 rounded-sm bg-surface animate-pulse" />
        </div>
        <div className="h-9 w-32 rounded-md bg-surface animate-pulse" />
      </div>

      <Panel>
        <SkeletonRows rows={6} />
      </Panel>
    </div>
  );
}
