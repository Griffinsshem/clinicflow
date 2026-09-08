"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Check } from "lucide-react";

import { CompleteDialog } from "@/components/follow-ups/CompleteDialog";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { timezoneOffsetMinutes } from "@/lib/client";
import { formatDate, relativeDays } from "@/lib/format";
import { useToast } from "@/providers/ToastProvider";
import type { FollowUp, GroupedFollowUps } from "@/types/api";


export default function FollowUpsPage() {
  const toast = useToast();
  const [completing, setCompleting] = useState<FollowUp | null>(null);

  const path = useMemo(
    () => `/follow-ups?grouped=true&tz_offset=${timezoneOffsetMinutes()}`,
    [],
  );

  const { data, loading, error, refetch } = useApi<GroupedFollowUps>(path);

  const outstanding =
    (data?.overdue.length ?? 0) + (data?.due_today.length ?? 0);

  function handleCompleted(scheduled: boolean) {
    setCompleting(null);
    toast(
      scheduled
        ? "Follow-up completed and next appointment booked."
        : "Follow-up completed.",
    );
    void refetch();
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          Follow-ups
        </h1>
        <p className="mt-0.5 text-ink-muted">
          {loading
            ? "\u00A0"
            : outstanding === 0
              ? "Nothing needs attention today."
              : `${outstanding} ${outstanding === 1 ? "patient needs" : "patients need"} attention.`}
        </p>
      </header>

      {error ? (
        <Panel>
          <ErrorState message={error} onRetry={refetch} />
        </Panel>
      ) : loading || !data ? (
        <>
          <Panel>
            <SkeletonRows rows={3} />
          </Panel>
          <Panel>
            <SkeletonRows rows={2} />
          </Panel>
        </>
      ) : (
        <>
          <Section
            title="Overdue"
            tone="brick"
            followUps={data.overdue}
            emptyTitle="Nothing overdue"
            emptyDescription="Follow-ups past their date will appear here."
            onComplete={setCompleting}
          />

          <Section
            title="Due today"
            tone="ochre"
            followUps={data.due_today}
            emptyTitle="Nothing due today"
            emptyDescription="Follow-ups dated today will appear here."
            onComplete={setCompleting}
          />

          <Section
            title="Upcoming"
            tone="neutral"
            followUps={data.upcoming}
            emptyTitle="Nothing scheduled ahead"
            emptyDescription="Add a follow-up from a patient's page."
            onComplete={setCompleting}
          />

          {data.completed.length > 0 && (
            <Panel>
              <PanelHeader title="Recently completed" />
              <ul className="divide-y divide-hairline">
                {data.completed.map((followUp) => (
                  <li
                    key={followUp.id}
                    className="flex items-start justify-between gap-3 px-4 py-3"
                  >
                    <div className="min-w-0">
                      <PatientLink followUp={followUp} muted />
                      <p className="truncate text-sm text-ink-subtle">
                        {followUp.reason}
                      </p>
                    </div>
                    <Badge tone="quiet">
                      {formatDate(followUp.follow_up_date)}
                    </Badge>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}

      <CompleteDialog
        followUp={completing}
        onDone={handleCompleted}
        onCancel={() => setCompleting(null)}
      />
    </div>
  );
}

function Section({
  title,
  tone,
  followUps,
  emptyTitle,
  emptyDescription,
  onComplete,
}: {
  title: string;
  tone: "brick" | "ochre" | "neutral";
  followUps: FollowUp[];
  emptyTitle: string;
  emptyDescription: string;
  onComplete: (followUp: FollowUp) => void;
}) {
  return (
    <Panel>
      <PanelHeader
        title={title}
        action={
          followUps.length > 0 ? (
            <span className="text-sm text-ink-muted tabular">
              {followUps.length}
            </span>
          ) : undefined
        }
      />

      {followUps.length === 0 ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <ul className="divide-y divide-hairline">
          {followUps.map((followUp) => (
            <li
              key={followUp.id}
              className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3"
            >
              <div className="min-w-0 flex-1">
                <PatientLink followUp={followUp} />
                <p className="truncate text-sm text-ink-muted">
                  {followUp.reason}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge tone={tone}>
                  {tone === "brick"
                    ? relativeDays(followUp.follow_up_date)
                    : formatDate(followUp.follow_up_date)}
                </Badge>

                <Button size="sm" onClick={() => onComplete(followUp)}>
                  <Check className="h-3.5 w-3.5" aria-hidden="true" />
                  Complete
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function PatientLink({
  followUp,
  muted = false,
}: {
  followUp: FollowUp;
  muted?: boolean;
}) {
  return (
    <Link
      href={`/patients/${followUp.patient_id}`}
      className={`truncate font-medium hover:underline ${
        muted ? "text-ink-muted" : "text-ink"
      }`}
    >
      {followUp.patient?.full_name ?? "Unknown patient"}
    </Link>
  );
}
