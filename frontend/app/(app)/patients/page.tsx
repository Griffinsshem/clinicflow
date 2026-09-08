"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useMemo, useState } from "react";
import { PatientForm } from "@/components/patients/PatientForm";
import { PatientList } from "@/components/patients/PatientList";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Pagination } from "@/components/ui/Pagination";
import { Panel } from "@/components/ui/Panel";
import { SearchInput } from "@/components/ui/SearchInput";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { useToast } from "@/providers/ToastProvider";
import type { Patient } from "@/types/api";

export default function PatientsPage() {
  return (
    <Suspense fallback={null}>
      <PatientsView />
    </Suspense>
  );
}

function PatientsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  const [adding, setAdding] = useState(false);
  const search = searchParams.get("search") ?? "";
  const page = Number(searchParams.get("page") ?? 1);

  const updateQuery = useCallback(
    (changes: Record<string, string | number | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(changes)) {
        if (value === null || value === "") params.delete(key);
        else params.set(key, String(value));
      }
      router.replace(`/patients?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const path = useMemo(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (page > 1) params.set("page", String(page));
    const query = params.toString();
    return `/patients${query ? `?${query}` : ""}`;
  }, [search, page]);

  const { data, meta, loading, error, refetch } = useApi<Patient[]>(path);

  function handleSaved(patient: Patient) {
    setAdding(false);
    toast(`${patient.full_name} added.`);
    void refetch();
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            Patients
          </h1>
          <p className="mt-0.5 text-ink-muted tabular">
            {meta ? `${meta.total} on record` : "\u00A0"}
          </p>
        </div>

        <Button variant="primary" onClick={() => setAdding(true)}>
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add patient
        </Button>
      </header>

      <div className="max-w-sm">
        <SearchInput
          value={search}
          onChange={(value) => updateQuery({ search: value, page: null })}
          placeholder="Search by name, phone, or email"
        />
      </div>

      <Panel>
        {error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : loading ? (
          <SkeletonRows rows={6} />
        ) : !data?.length ? (
          search ? (
            <EmptyState
              title="No matches"
              description={`Nothing found for "${search}". Try a different name or number.`}
            />
          ) : (
            <EmptyState
              title="No patients yet"
              description="Add your first patient to start scheduling appointments."
              action={
                <Button variant="primary" onClick={() => setAdding(true)}>
                  Add patient
                </Button>
              }
            />
          )
        ) : (
          <>
            <PatientList patients={data} />
            {meta && (
              <Pagination
                meta={meta}
                onChange={(next) => updateQuery({ page: next })}
              />
            )}
          </>
        )}
      </Panel>

      <Modal
        open={adding}
        onClose={() => setAdding(false)}
        title="Add patient"
      >
        <PatientForm
          onSaved={handleSaved}
          onCancel={() => setAdding(false)}
        />
      </Modal>
    </div>
  );
}
