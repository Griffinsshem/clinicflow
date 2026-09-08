import { Button } from "./Button";

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div aria-hidden="true" className="divide-y divide-hairline">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex items-center gap-4 px-4 py-3">
          <div className="h-4 w-40 rounded-sm bg-ground animate-pulse" />
          <div className="h-4 w-24 rounded-sm bg-ground animate-pulse" />
          <div className="ml-auto h-4 w-16 rounded-sm bg-ground animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-base font-medium text-ink">{title}</p>
      <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">
        {description}
      </p>
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-base font-medium text-ink">Couldn&apos;t load this</p>
      <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">{message}</p>
      {onRetry && (
        <div className="mt-4 flex justify-center">
          <Button onClick={onRetry}>Try again</Button>
        </div>
      )}
    </div>
  );
}
