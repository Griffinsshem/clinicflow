"use client";

import { createContext, useContext } from "react";

import type { Session } from "@/types/api";

const SessionContext = createContext<Session | null>(null);

export function SessionProvider({
  session,
  children,
}: {
  session: Session;
  children: React.ReactNode;
}) {
  return (
    <SessionContext.Provider value={session}>{children}</SessionContext.Provider>
  );
}

export function useSession(): Session {
  const session = useContext(SessionContext);
  if (!session) {
    throw new Error("useSession must be used inside SessionProvider");
  }
  return session;
}
