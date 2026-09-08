"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useActionState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";


interface FormState {
  message?: string;
  errors: Record<string, string>;
}

const EMPTY: FormState = { errors: {} };

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextParam = searchParams.get("next");
  const destination =
    nextParam && nextParam.startsWith("/") && !nextParam.startsWith("//")
      ? nextParam
      : "/dashboard";

  const [state, formAction, pending] = useActionState(
    async (_previous: FormState, formData: FormData): Promise<FormState> => {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });

      const body = await response.json().catch(() => null);

      if (!body?.success) {
        return {
          message: body?.message ?? "Something went wrong. Please try again.",
          errors: body?.errors ?? {},
        };
      }

      router.refresh();
      router.push(destination);
      return EMPTY;
    },
    EMPTY,
  );

  return (
    <form action={formAction} className="space-y-4">
      {state.message && (
        <div
          role="alert"
          className="rounded-md border border-brick/25 bg-brick-soft px-3 py-2 text-sm text-brick"
        >
          {state.message}
        </div>
      )}

      <Field label="Email" error={state.errors.email} required>
        {(props) => (
          <input
            {...props}
            name="email"
            type="email"
            autoComplete="email"
            required
            autoFocus
          />
        )}
      </Field>

      <Field label="Password" error={state.errors.password} required>
        {(props) => (
          <input
            {...props}
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        )}
      </Field>

      <Button
        type="submit"
        variant="primary"
        loading={pending}
        className="w-full"
      >
        Sign in
      </Button>

      <p className="text-center text-sm text-ink-muted">
        No account yet?{" "}
        <Link href="/register" className="font-medium text-accent hover:underline">
          Create a clinic
        </Link>
      </p>
    </form>
  );
}
