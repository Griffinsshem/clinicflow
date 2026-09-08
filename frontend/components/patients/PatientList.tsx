import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { formatDate } from "@/lib/format";
import type { Patient } from "@/types/api";

export function PatientList({ patients }: { patients: Patient[] }) {
  return (
    <ul className="divide-y divide-hairline">
      {patients.map((patient) => (
        <li key={patient.id}>
          <Link
            href={`/patients/${patient.id}`}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-ground"
          >
            <div className="grid min-w-0 flex-1 gap-x-4 gap-y-0.5 sm:grid-cols-[2fr_1.5fr_1fr] sm:items-center">
              <p className="truncate font-medium text-ink">{patient.full_name}</p>

              <p className="truncate text-sm text-ink-muted tabular">
                {patient.phone ?? "No phone recorded"}
              </p>

              <p className="hidden text-sm text-ink-muted sm:block tabular">
                {patient.date_of_birth
                  ? formatDate(patient.date_of_birth)
                  : "—"}
              </p>
            </div>

            <ChevronRight
              className="h-4 w-4 shrink-0 text-ink-subtle"
              aria-hidden="true"
            />
          </Link>
        </li>
      ))}
    </ul>
  );
}
