import { Button } from "./Button";
import type { PaginationMeta } from "@/types/api";

export function Pagination({
  meta,
  onChange,
}: {
  meta: PaginationMeta;
  onChange: (page: number) => void;
}) {
  if (meta.pages <= 1) return null;

  const from = (meta.page - 1) * meta.limit + 1;
  const to = Math.min(meta.page * meta.limit, meta.total);

  return (
    <div className="flex items-center justify-between gap-4 border-t border-hairline px-4 py-3">
      <p className="text-sm text-ink-muted tabular">
        {from}–{to} of {meta.total}
      </p>
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={meta.page <= 1}
          onClick={() => onChange(meta.page - 1)}
        >
          Previous
        </Button>
        <Button
          size="sm"
          disabled={meta.page >= meta.pages}
          onClick={() => onChange(meta.page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
