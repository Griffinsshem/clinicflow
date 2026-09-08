"use client";

import { useMemo } from "react";

import { AttentionList } from "@/components/dashboard/AttentionList";
import {
  MetricStrip,
  MetricStripSkeleton,
} from "@/components/dashboard/MetricStrip";
import { TodaySchedule } from "@/components/dashboard/TodaySchedule";
import { WeeklyActivity } from "@/components/dashboard/WeeklyActivity";
import { Panel } from "@/components/ui/Panel";
import { ErrorState, SkeletonRows } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { timezoneOffsetMinutes } from "@/lib/client";
import type { DashboardData } from "@/types/api";

export default function DashboardPage() {
  const path = useMemo(
    () => `/dashboard?tz_offset=${timezoneOffsetMinutes()}`,
    [],
  );

  const { data, loading, error, refetch } = useApi<DashboardData>(path);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          Dashboard
        </h1>
        <p className="mt-0.5 text-ink-muted">
          Today at a glance, and who still needs seeing.
        </p>
      </header>

      {error ? (
        <Panel>
          <ErrorState message={error} onRetry={refetch} />
        </Panel>
      ) : loading || !data ? (
        <DashboardSkeleton />
      ) : (
        <>
          <MetricStrip metrics={data.metrics} />
          <div className="grid gap-6 lg:grid-cols-2 items-start">
            <TodaySchedule appointments={data.today_schedule} />
            <AttentionList followUps={data.attention_follow_ups} />
          </div>

          <WeeklyActivity days={data.weekly_activity} />
        </>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <>
      <MetricStripSkeleton />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <SkeletonRows rows={4} />
        </Panel>
        <Panel>
          <SkeletonRows rows={3} />
        </Panel>
      </div>
    </>
  );
}
