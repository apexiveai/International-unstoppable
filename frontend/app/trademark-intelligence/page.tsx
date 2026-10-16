"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import {
  ArrowRight,
  FileSearch,
  History,
  ScanSearch,
  ShieldCheck,
  Upload,
} from "lucide-react";
import RequireSubscription from "@/components/RequireSubscription";
import TrademarkProductLaunchButton from "@/components/TrademarkProductLaunchButton";
import TrademarkWorkspace from "@/components/TrademarkWorkspace";

function subscribeToAdminRole(listener: () => void) {
  window.addEventListener("storage", listener);
  return () => window.removeEventListener("storage", listener);
}

function getAdminRoleSnapshot() {
  try {
    const storedUser = localStorage.getItem("apexive_user");
    return storedUser
      ? Boolean((JSON.parse(storedUser) as { is_admin?: boolean }).is_admin)
      : false;
  } catch {
    return false;
  }
}

const features = [
  {
    icon: Upload,
    title: "Two-file upload",
    description:
      "Compare PDF, JPG, JPEG, PNG, or WEBP trademark files up to 20 MB each.",
  },
  {
    icon: ScanSearch,
    title: "Visual similarity screening",
    description:
      "Find visually matching regions between the two submitted documents.",
  },
  {
    icon: FileSearch,
    title: "Evidence and export",
    description:
      "Review annotated original pages, inspect match scores, and download a JSON report.",
  },
  {
    icon: History,
    title: "Company check history",
    description:
      "Reopen previous checks saved to your company account.",
  },
];

const workflow = [
  "Upload two files",
  "Compare visually",
  "Review evidence",
  "Export report",
];

export default function TrademarkConflictPage() {
  const isAdmin = useSyncExternalStore(
    subscribeToAdminRole,
    getAdminRoleSnapshot,
    () => false,
  );

  if (isAdmin) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-950 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-2xl font-bold">Trademark Conflict</h1>
            <Link
              href="/admin"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Admin dashboard
            </Link>
          </div>
          <TrademarkWorkspace />
        </div>
      </main>
    );
  }

  return (
    <RequireSubscription productKey="trademark">
      <main className="min-h-screen bg-slate-50 text-slate-950">

        {/* Hero */}

        <section className="border-b border-slate-200 bg-white">

          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8 lg:py-20">

            <div className="max-w-4xl">

              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">

                <ShieldCheck className="h-4 w-4" />

                Apexive AI

              </div>

              <h1 className="mt-7 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">

                Trademark Conflict

              </h1>

              <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">

                Screen two trademark files for visual similarity, review
                annotated match evidence, and keep checks organized in your
                company history.

              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">

                <a
                  href="#workspace"

                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 py-4 text-sm font-semibold text-white transition hover:bg-slate-800"

                >

                  Start a visual check

                  <ArrowRight className="h-4 w-4" />

                </a>

                <div className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-6 py-4 text-sm font-medium text-slate-600">

                  Pairwise visual comparison

                </div>

              </div>

            </div>

          </div>

        </section>

        <TrademarkWorkspace />

        {/* Metrics / Capability */}

        <section className="mx-auto max-w-7xl px-6 py-12 lg:px-8">

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            <MetricCard

              label="Supported files"
              value="PDF / Images"
              description="PDF, JPG, PNG, WEBP"

            />

            <MetricCard

              label="Upload limit"
              value="20 MB"
              description="Per file"

            />

            <MetricCard

              label="Analysis"
              value="Visual"
              description="Similarity screening"

            />

            <MetricCard

              label="Report export"
              value="JSON"
              description="Downloadable check data"
            />

          </div>

        </section>

        {/* Workflow */}

        <section className="mx-auto max-w-7xl px-6 pb-12 lg:px-8">

          <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm lg:p-9">

            <div>

              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">

                How it works

              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-tight">

                Compare, review, and save a visual check

              </h2>

            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

              {workflow.map((step, index) => (

                <div

                  key={step}

                  className="relative rounded-2xl border border-slate-200 bg-slate-50 p-5"

                >

                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-xs font-bold text-white">

                    {index + 1}

                  </div>

                  <p className="mt-4 text-sm font-semibold text-slate-900">

                    {step}

                  </p>

                </div>

              ))}

            </div>

          </div>

        </section>

        {/* Features */}

        <section className="mx-auto max-w-7xl px-6 pb-16 lg:px-8 lg:pb-20">

          <div className="mb-8">

            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">

              Platform Capabilities

            </p>

            <h2 className="mt-2 text-3xl font-bold tracking-tight">

              Trademark Conflict visual screening

            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">

              Compare two files to surface visual matches. This screening is
              an investigative aid, not a legal opinion or a determination of
              trademark confusion.

            </p>

          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">

            {features.map((feature) => {

              const Icon = feature.icon;

              return (

                <div

                  key={feature.title}

                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"

                >

                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-white">

                    <Icon className="h-5 w-5" />

                  </div>

                  <h3 className="mt-5 text-lg font-semibold">

                    {feature.title}

                  </h3>

                  <p className="mt-2 text-sm leading-6 text-slate-600">

                    {feature.description}

                  </p>

                </div>

              );

            })}

          </div>

        </section>

        {/* Launch CTA */}

        <section className="border-t border-slate-200 bg-white">

          <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">

            <div className="flex flex-col gap-6 rounded-3xl bg-slate-950 p-8 text-white lg:flex-row lg:items-center lg:justify-between lg:p-10">

              <div>

                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">

                  Ready to investigate?

                </p>

                <h2 className="mt-3 text-2xl font-bold">

                  Open Trademark Conflict

                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">

                  Open the dedicated workspace to run a new visual comparison
                  and continue your investigation.

                </p>

              </div>

              <TrademarkProductLaunchButton />

            </div>

          </div>

        </section>

      </main>
    </RequireSubscription>
  );

}
function MetricCard({

  label,

  value,

  description,

}: {

  label: string;

  value: string;

  description: string;

}) {

  return (

    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">

        {label}

      </p>

      <div className="mt-3 text-2xl font-bold tracking-tight">

        {value}

      </div>

      <p className="mt-1 text-sm text-slate-500">

        {description}

      </p>

    </div>

  );

}