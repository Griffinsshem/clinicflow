import Link from "next/link";

import { Logo, LogoMark } from "@/components/Logo";
import { DemoButton } from "@/components/landing/DemoButton";
import { HeroPanel } from "@/components/landing/HeroPanel";

export const metadata = {
  title: "ClinicFlow — appointment and follow-up management for small clinics",
  description:
    "Keep track of appointments, and of the patients who need seeing again. Built for small clinics.",
};

export default function LandingPage() {
  return (
    <div className="min-h-dvh">
      <SiteHeader />

      <main>
        <Hero />
        <Problem />
        <HowItWorks />
      </main>

      <SiteFooter />
    </div>
  );
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-hairline bg-surface/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 md:px-6">
        <Logo />

        <nav className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm font-medium text-ink-muted transition-colors hover:text-ink"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="inline-flex h-8 items-center rounded-md bg-accent px-3 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
          >
            Create a clinic
          </Link>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-16 md:px-6 md:py-24">
      <div className="grid items-center gap-10 lg:grid-cols-[1fr_1.1fr] lg:gap-14">
        <div>
          <h1 className="text-3xl font-semibold leading-tight tracking-tight text-ink md:text-4xl">
            A calmer way to manage clinic appointments.
          </h1>

          <p className="mt-4 max-w-md text-lg leading-relaxed text-ink-muted">
            ClinicFlow keeps your schedule in one place — and makes sure the
            patients who need seeing again actually get seen.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <DemoButton />
            <Link
              href="/register"
              className="inline-flex h-9 items-center rounded-md border border-line bg-surface px-4 font-medium text-ink transition-colors hover:bg-ground"
            >
              Create a clinic
            </Link>
          </div>

          <p className="mt-3 text-sm text-ink-subtle">
            The demo opens a private clinic with sample data. Nothing to set up.
          </p>
        </div>

        <HeroPanel />
      </div>
    </section>
  );
}

function Problem() {
  return (
    <section className="border-y border-hairline bg-surface">
      <div className="mx-auto max-w-5xl px-4 py-14 md:px-6 md:py-20">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-ink">
            Patients slip through the gaps
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-ink-muted">
            Most small clinics run on a paper diary, a phone, and someone&apos;s
            memory. That works for today&apos;s appointments. It does not work
            for the patient who was told to come back in six weeks.
          </p>
        </div>

        
        <dl className="mt-10 grid gap-x-10 gap-y-8 border-t border-hairline pt-8 sm:grid-cols-3">
          {[
            {
              term: "Follow-ups get forgotten",
              detail:
                "A note in a diary is only found if someone thinks to look for it.",
            },
            {
              term: "No view of the week",
              detail:
                "Knowing how busy Thursday is means counting entries by hand.",
            },
            {
              term: "Records take time to find",
              detail:
                "Looking up a patient's history interrupts whoever is at the desk.",
            },
          ].map(({ term, detail }) => (
            <div key={term}>
              <dt className="font-medium text-ink">{term}</dt>
              <dd className="mt-1.5 text-ink-muted">{detail}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      title: "Add the patient",
      detail:
        "Name and a phone number is enough to start. Everything else is optional.",
    },
    {
      title: "Book the appointment",
      detail:
        "Confirm it, complete it, or mark a no-show as the day goes on.",
    },
    {
      title: "Set the follow-up",
      detail:
        "Record when they need seeing again, and why.",
    },
    {
      title: "It comes back to you",
      detail:
        "Due and overdue follow-ups surface on the dashboard. Complete one and book the next visit in the same step.",
    },
  ];

  return (
    <section className="mx-auto max-w-5xl px-4 py-14 md:px-6 md:py-20">
      <h2 className="text-2xl font-semibold tracking-tight text-ink">
        How it works
      </h2>

      <ol className="mt-8 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((step, index) => (
          <li key={step.title} className="border-t border-line pt-4">
            <span className="text-sm font-medium tabular text-ink-subtle">
              {index + 1}
            </span>
            <h3 className="mt-2 font-medium text-ink">{step.title}</h3>
            <p className="mt-1.5 text-ink-muted">{step.detail}</p>
          </li>
        ))}
      </ol>

      <div className="mt-12 flex flex-wrap items-center gap-3 border-t border-hairline pt-8">
        <DemoButton />
        <p className="text-sm text-ink-muted">
          Or{" "}
          <Link href="/register" className="font-medium text-accent hover:underline">
            create your own clinic
          </Link>
          .
        </p>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-hairline bg-surface">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-6 md:px-6">
        <div className="flex items-center gap-2">
          <LogoMark className="h-4 w-4 text-ink-subtle" />
          <p className="text-sm text-ink-muted">
            A portfolio project. Sample data is fictional.
          </p>
        </div>
        <a
          href="https://github.com/Griffinsshem/clinicflow"
          className="text-sm font-medium text-accent hover:underline"
        >
          Source on GitHub
        </a>
      </div>
    </footer>
  );
}
