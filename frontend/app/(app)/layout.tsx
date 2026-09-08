import { redirect } from "next/navigation";

import { Nav } from "@/components/layout/Nav";
import { ToastProvider } from "@/providers/ToastProvider";
import { UserMenu } from "@/components/layout/UserMenu";
import { callBackend } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { Session } from "@/types/api";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const token = await getSessionToken();
  if (!token) redirect("/login");

  const { body } = await callBackend<Session>("/auth/me", {}, token);
  if (!body.success) redirect("/login");

  const session = body.data;

  return (
    <ToastProvider>
    <div className="flex min-h-dvh">
      <Nav />

      <div className="flex flex-1 flex-col min-w-0">
        <header className="h-14 shrink-0 flex items-center justify-between gap-4 border-b border-hairline bg-surface px-4 md:px-6">
          <span className="font-semibold tracking-tight text-ink md:hidden">
            ClinicFlow
          </span>
          <div className="ml-auto">
            <UserMenu session={session} />
          </div>
        </header>

        <main className="flex-1 px-4 py-6 pb-20 md:px-6 md:pb-8">
          <div className="mx-auto w-full max-w-5xl">{children}</div>
        </main>
      </div>
    </div>
    </ToastProvider>
  );
}
