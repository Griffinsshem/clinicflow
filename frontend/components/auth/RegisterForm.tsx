"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useActionState } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";

const PASSWORD_MIN_LENGTH = 10;

interface FormState {
  message?: string;
  errors: Record<string, string>;
}

const EMPTY: FormState = { errors: {} };

export function RegisterForm() {
  const router = useRouter();

  const [state, formAction, pending] = useActionState(
    async (_previous: FormState, formData: FormData): Promise<FormState> => {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinic_name: formData.get("clinic_name"),
          full_name: formData.get("full_name"),
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
      router.push("/dashboard");
      return EMPTY;
    },
    EMPTY,
  );

  return (
    <form action={formAction} className="space-y-4">
      {state.message && !Object.keys(state.errors).length && (
        <div
          role="alert"
          className="rounded-md border border-brick/25 bg-brick-soft px-3 py-2 text-sm text-brick"
        >
          {state.message}
        </div>
      )}

      <Field label="Clinic name" error={state.errors.clinic_name} required>
        {(props) => (
          <input
            {...props}
            name="clinic_name"
            required
            minLength={2}
            maxLength={120}
            autoFocus
          />
        )}
      </Field>

      <Field label="Your name" error={state.errors.full_name} required>
        {(props) => (
          <input
            {...props}
            name="full_name"
            autoComplete="name"
            required
            minLength={2}
            maxLength={120}
          />
        )}
      </Field>

      <Field label="Email" error={state.errors.email} required>
        {(props) => (
          <input {...props} name="email" type="email" autoComplete="email" required />
        )}
      </Field>

      <Field
        label="Password"
        error={state.errors.password}
        hint={`At least ${PASSWORD_MIN_LENGTH} characters.`}
        required
      >
        {(props) => (
          <input
            {...props}
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={PASSWORD_MIN_LENGTH}
          />
        )}
      </Field>

      <Button type="submit" variant="primary" loading={pending} className="w-full">
        Create clinic
      </Button>

      <p className="text-center text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
