export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-dvh flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <span className="text-xl font-semibold tracking-tight text-ink">
            ClinicFlow
          </span>
        </div>
        {children}
      </div>
    </main>
  );
}
