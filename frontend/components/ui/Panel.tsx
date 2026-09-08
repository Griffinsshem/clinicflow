import { cx } from "@/lib/utils";

export function Panel({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={cx(
        "bg-surface border border-hairline rounded-lg",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function PanelHeader({
  title,
  action,
}: {
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="flex items-center justify-between gap-4 px-4 py-3 border-b border-hairline">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {action}
    </header>
  );
}
