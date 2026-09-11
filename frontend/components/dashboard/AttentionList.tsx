import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { EmptyState } from "@/components/ui/States";
import { relativeDays } from "@/lib/format";
import type { FollowUp } from "@/types/api";

export function AttentionList({ followUps }: { followUps: FollowUp[] }) {
  return (
    <Panel>
      <PanelHeader
        title="Needs attention"
        action={
          <Link
            href="/follow-ups"
            className="text-sm font-medium text-accent hover:underline"
          >
            All follow-ups
          </Link>
        }
      />

      {followUps.length === 0 ? (
        <EmptyState
          title="Nothing outstanding"
          description="Follow-ups that are overdue or due today will surface here."
        />
      ) : (
        <ul className="divide-y divide-hairline">
          {followUps.map((followUp) => (
            <li key={followUp.id}>
              <Link
                href={`/patients/${followUp.patient_id}`}
                className="flex items-start gap-3 px-4 py-3 hover:bg-ground transition-colors duration-150"
              >
                <Avatar name={followUp.patient?.full_name ?? "?"} size="sm" />

                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-ink">
                    {followUp.patient?.full_name ?? "Unknown patient"}
                  </p>
                  <p className="truncate text-sm text-ink-muted">
                    {followUp.reason}
                  </p>
                </div>

                <div className="shrink-0 text-right">
                  <Badge tone={followUp.is_overdue ? "brick" : "ochre"}>
                    {followUp.is_overdue ? "Overdue" : "Due today"}
                  </Badge>
                  {followUp.is_overdue && (
                    <p className="mt-1 text-xs text-ink-subtle">
                      {relativeDays(followUp.follow_up_date)}
                    </p>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
