export const metadata = { title: "Dashboard · ClinicFlow" };

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Dashboard
      </h1>
      <p className="mt-1 text-ink-muted">
        Signed in. Metrics and today&apos;s schedule land here next.
      </p>
    </div>
  );
}
