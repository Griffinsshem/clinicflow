import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata = { title: "Create a clinic · ClinicFlow" };

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Create your clinic
      </h1>
      <p className="mt-1 mb-6 text-ink-muted">
        You&apos;ll be the first administrator on the account.
      </p>
      <RegisterForm />
    </>
  );
}
