import { Suspense } from "react";

import { LoginForm } from "@/components/auth/LoginForm";

export const metadata = { title: "Sign in · ClinicFlow" };

export default function LoginPage() {
  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Sign in
      </h1>
      <p className="mt-1 mb-6 text-ink-muted">
        Continue to your clinic dashboard.
      </p>
      <Suspense>
        <LoginForm />
      </Suspense>
    </>
  );
}
