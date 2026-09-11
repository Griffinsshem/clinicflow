import Link from "next/link";
import {
  CalendarDays,
  LayoutDashboard,
  RotateCcw,
  Users,
} from "lucide-react";

import { Logo, LogoMark } from "@/components/Logo";
import { DemoButton } from "@/components/landing/DemoButton";
import { ProductPreview } from "@/components/landing/ProductPreview";

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
        <Facts />
        <Features />
        <HowItWorks />
        <ClosingCta />
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
    <section className="border-b border-hairline bg-surface">
      <div className="mx-auto max-w-5xl px-4 pt-14 md:px-6 md:pt-20">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-ink md:text-5xl">
            Nobody falls through
            <br />
            <span className="font-serif italic font-normal text-accent">
              the cracks
            </span>
          </h1>

          <p className="mx-auto mt-5 max-w-lg text-lg leading-relaxed text-ink-muted">
            Appointments, visit history and follow-ups in one place — so the
            patient who needs seeing again actually gets seen.
          </p>

          <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
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
        <div className="mx-auto mt-12 max-w-4xl pb-16 md:pb-20">
          <ProductPreview />
        </div>
      </div>
    </section>
  );
}

function Facts() {
  const facts = [
    { value: "5", label: "Appointment statuses tracked" },
    { value: "1", label: "Click from a completed visit to the next booking" },
    { value: "0", label: "Follow-ups that quietly disappear" },
  ];

  return (
    <section className="border-b border-hairline">
      <dl className="mx-auto grid max-w-5xl divide-y divide-hairline px-4 sm:grid-cols-3 sm:divide-x sm:divide-y-0 md:px-6">
        {facts.map(({ value, label }) => (
          <div key={label} className="px-2 py-7 text-center">
            <dt className="text-3xl font-semibold tabular text-ink">{value}</dt>
            <dd className="mx-auto mt-1 max-w-[14rem] text-sm text-ink-muted">
              {label}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Features() {
  const features = [
    {
      icon: Users,
      title: "Patient records",
      detail:
        "Name and a phone number is enough to start. Search by any of it, and see a full visit history on one page.",
    },
    {
      icon: CalendarDays,
      title: "Appointments",
      detail:
        "Book, confirm, complete or mark a no-show. Filter by date, status or type without leaving the schedule.",
    },
    {
      icon: RotateCcw,
      title: "Follow-ups",
      detail:
        "Record when someone needs seeing again. Overdue and due-today surface on their own, in a list you work through.",
    },
    {
      icon: LayoutDashboard,
      title: "Daily overview",
      detail:
        "Today's schedule, outstanding follow-ups and the shape of the week — the four things worth knowing on arrival.",
    },
  ];

  return (
    <section className="border-b border-hairline bg-surface">
      <div className="mx-auto max-w-5xl px-4 py-16 md:px-6 md:py-20">
        <div className="lg:grid lg:grid-cols-[minmax(0,20rem)_1fr] lg:gap-12">
        <div className="lg:sticky lg:top-24 lg:self-start">
          <h2 className="text-3xl font-semibold tracking-tight text-ink">
            Four things,{" "}
            <span className="font-serif italic font-normal text-accent">
              done properly
            </span>
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-ink-muted">
            Not a hospital system. A clinic needs to know who is coming, who came,
            and who still needs to.
          </p>
        </div>

        <div className="mt-10 grid gap-x-10 gap-y-9 sm:grid-cols-2 lg:mt-0">
          {features.map(({ icon: Icon, title, detail }) => (
            <div key={title} className="border-t border-line pt-5">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-accent-soft text-accent">
                <Icon className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="mt-3 font-medium text-ink">{title}</h3>
              <p className="mt-1.5 leading-relaxed text-ink-muted">{detail}</p>
            </div>
          ))}
        </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { title: "Add the patient", detail: "A name and a number is enough." },
    { title: "Book the appointment", detail: "Confirm or complete it as the day goes on." },
    { title: "Set the follow-up", detail: "When they need seeing again, and why." },
    { title: "It comes back to you", detail: "Due and overdue surface on the dashboard." },
  ];

  return (
    <section className="border-b border-hairline">
      <div className="mx-auto max-w-5xl px-4 py-16 md:px-6 md:py-20">
        <h2 className="text-3xl font-semibold tracking-tight text-ink">
          How it works
        </h2>

        <ol className="mt-9 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <li key={step.title} className="border-t border-line pt-4">
              <span className="text-sm font-medium tabular text-ink-subtle">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-2 font-medium text-ink">{step.title}</h3>
              <p className="mt-1.5 text-ink-muted">{step.detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function ClosingCta() {
  return (
    <section className="bg-surface">
      <div className="mx-auto max-w-5xl px-4 py-16 text-center md:px-6 md:py-20">
        <h2 className="text-2xl font-semibold tracking-tight text-ink">
          Have a look around
        </h2>
        <p className="mx-auto mt-2 max-w-md text-ink-muted">
          The demo is a real clinic with sample patients, appointments and
          follow-ups. It is yours alone and takes one click.
        </p>
        <div className="mt-6 flex justify-center">
          <DemoButton />
        </div>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-hairline">
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
