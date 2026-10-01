"use client";

import {

  ArrowRight,


  FileSearch,

  FolderSearch,

  Gavel,

  History,

  ScanSearch,

  ShieldCheck,

  Upload,

} from "lucide-react";
import RequireSubscription from "@/components/RequireSubscription";

const detectorUrl = process.env.NEXT_PUBLIC_TRADEMARK_DETECTOR_URL?.trim();

const features = [

  {

    icon: Upload,

    title: "Document Intake",

    description:

      "Upload government trademark journals and client trademark lists for investigation.",

  },

  {

    icon: ScanSearch,

    title: "Conflict Detection",

    description:

      "Identify application, company, phone and trademark conflicts across submitted records.",

  },

  {

    icon: FolderSearch,

    title: "Case Management",

    description:

      "Group detected signals into investigation cases for structured review.",

  },

  {

    icon: Gavel,

    title: "Human Review",

    description:

      "Confirm or reject detected conflicts and preserve reviewer comments.",

  },

  {

    icon: FileSearch,

    title: "Evidence & Reports",

    description:

      "Review source evidence and generate a formal conflict investigation report.",

  },

  {

    icon: History,

    title: "Report History",

    description:

      "Keep generated investigation reports available for later reference.",

  },

];

const workflow = [

  "Upload",

  "Detect",

  "Group into Cases",

  "Review",

  "Confirm / Reject",

  "Report",

];

export default function TrademarkIntelligencePage() {
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

                Trademark Intelligence

              </h1>

              <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">

                Investigate potential trademark conflicts across government

                trademark journals and client trademark records with a

                structured AI-assisted workflow.

              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">

                {detectorUrl ? <a

                  href={detectorUrl}

                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 py-4 text-sm font-semibold text-white transition hover:bg-slate-800"

                >

                  Launch Trademark Detector

                  <ArrowRight className="h-4 w-4" />

                </a> : (
                  <p role="alert" className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-3 text-sm text-amber-200">
                    Trademark Detector is not configured. Set
                    NEXT_PUBLIC_TRADEMARK_DETECTOR_URL in Vercel.
                  </p>
                )}

                <div className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-6 py-4 text-sm font-medium text-slate-600">

                  Trademark Conflict Investigation

                </div>

              </div>

            </div>

          </div>

        </section>

        {/* Metrics / Capability */}

        <section className="mx-auto max-w-7xl px-6 py-12 lg:px-8">

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            <MetricCard

              label="Government Journal"

              value="PDF"

              description="Source document"

            />

            <MetricCard

              label="Client Records"

              value="XLSX / PDF"

              description="Trademark portfolio"

            />

            <MetricCard

              label="Investigation"

              value="AI"

              description="Conflict analysis"

            />

            <MetricCard

              label="Final Output"

              value="PDF"

              description="Investigation report"
            />

          </div>

        </section>

        {/* Workflow */}

        <section className="mx-auto max-w-7xl px-6 pb-12 lg:px-8">

          <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm lg:p-9">

            <div>

              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">

                Investigation Workflow

              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-tight">

                From documents to reviewed conflict cases

              </h2>

            </div>

            <div className="mt-8 grid gap-3 md:grid-cols-3 lg:grid-cols-6">

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

              Trademark Conflict Investigation

            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">

              The investigation workspace remains a dedicated service while

              Apexive Community provides the entry point.

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

                  Open Trademark Conflict Detector

                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">

                  Start a new trademark conflict investigation using the

                  dedicated Apexive AI detector workspace.

                </p>

              </div>

              {detectorUrl ? <a

                href={detectorUrl}

                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-6 py-4 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"

              >

                Open Detector

                <ArrowRight className="h-4 w-4" />

              </a> : null}

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