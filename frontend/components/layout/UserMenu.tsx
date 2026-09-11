"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import type { Session } from "@/types/api";

export function UserMenu({ session }: { session: Session }) {
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function signOut() {
    setSigningOut(true);
    await fetch("/api/auth/logout", { method: "POST" });
    router.refresh();
    router.push("/");
  }

  return (
    <div className="flex items-center gap-3">
      <div className="hidden sm:block text-right leading-tight">
        <p className="text-sm font-medium text-ink">{session.user.full_name}</p>
        <p className="text-xs text-ink-muted">{session.clinic.name}</p>
      </div>
      <Button size="sm" onClick={signOut} loading={signingOut}>
        Sign out
      </Button>
    </div>
  );
}
