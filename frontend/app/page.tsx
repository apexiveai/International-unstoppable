import Link from "next/link";

import Image from "next/image";
import Reveal from "@/components/animations/Reveal";
import SiteHeader from "@/components/SiteHeader";

import {

  getFeaturedArticles,

  getFeaturedProjects,

  getFeaturedResources,

  type Article,

  type Project,

  type Resource,

} from "@/lib/api";

import API_URL from "@/lib/api";

type Thread = {

  id: number;

  title: string;

  slug: string;

  content: string;

  category_id: number;

  author_id: number;

  views: number;

  created_at: string;

  updated_at: string;

};

export const dynamic = "force-dynamic";

async function getLatestThreads(): Promise<Thread[]> {

  const response = await fetch(`${API_URL}/api/threads`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error(`Failed to load discussions (${response.status})`);

  }

  return response.json();

}

function formatDate(value: string) {

  return new Date(value).toLocaleDateString("en-US", {

    month: "short",

    day: "numeric",

    year: "numeric",

  });

}

function GlowOrb({

  className,

}: {

  className: string;

}) {

  return (

    <div

      aria-hidden="true"

      className={`pointer-events-none absolute rounded-full blur-3xl ${className}`}

    />

  );

}

export default async function HomePage() {

  const results = await Promise.allSettled([

    getFeaturedArticles(),

    getFeaturedProjects(),

    getFeaturedResources(),

    getLatestThreads(),

  ]);

  const [articlesResult, projectsResult, resourcesResult, threadsResult] =
    results;

  const dataErrors = results.flatMap((result, index) => {

    if (result.status === "fulfilled") {

      return [];

    }

    const sections = ["articles", "projects", "resources", "discussions"];

    console.error(`Unable to load homepage ${sections[index]}:`, result.reason);

    return [sections[index]];

  });

  const articles =
    articlesResult.status === "fulfilled" ? articlesResult.value : [];

  const projects =
    projectsResult.status === "fulfilled" ? projectsResult.value : [];

  const resources =
    resourcesResult.status === "fulfilled" ? resourcesResult.value : [];

  const threads =
    threadsResult.status === "fulfilled" ? threadsResult.value : [];

  const featuredArticles = articles.slice(0, 3);

  const featuredProjects = projects.slice(0, 3);

  const latestResources = resources.slice(0, 4);

  const latestThreads = threads.slice(0, 5);

  return (

    <div className="min-h-screen overflow-hidden bg-[#f7f9fc] text-slate-900">

      <style>{`

        @keyframes apexiveFloat {

          0%, 100% {

            transform: translate3d(0, 0, 0);

          }

          50% {

            transform: translate3d(0, -16px, 0);

          }

        }

        @keyframes apexiveFloatReverse {

          0%, 100% {

            transform: translate3d(0, 0, 0);

          }

          50% {

            transform: translate3d(12px, 12px, 0);

          }

        }

        @keyframes apexivePulse {

          0%, 100% {

            opacity: .35;

            transform: scale(1);

          }

          50% {

            opacity: .75;

            transform: scale(1.08);

          }

        }

        @keyframes apexiveScan {

          0% {

            transform: translateY(-100%);

            opacity: 0;

          }

          15% {

            opacity: .7;

          }

          85% {

            opacity: .7;

          }

          100% {

            transform: translateY(700%);

            opacity: 0;

          }

        }

        @keyframes apexiveGrid {

          from {

            background-position: 0 0, 0 0;

          }

          to {

            background-position: 40px 40px, 40px 40px;

          }

        }

        @keyframes apexiveShimmer {

          0% {

            background-position: -200% 0;

          }

          100% {

            background-position: 200% 0;

          }

        }

        @keyframes apexiveBlink {

          0%, 100% {

            opacity: 1;

          }

          50% {

            opacity: .35;

          }

        }

        .apexive-float {

          animation: apexiveFloat 7s ease-in-out infinite;

        }

        .apexive-float-reverse {

          animation: apexiveFloatReverse 9s ease-in-out infinite;

        }

        .apexive-pulse {

          animation: apexivePulse 4s ease-in-out infinite;

        }

        .apexive-scan {

          animation: apexiveScan 7s linear infinite;

        }

        .apexive-grid {

          background-image:

            linear-gradient(rgba(59,130,246,.06) 1px, transparent 1px),

            linear-gradient(90deg, rgba(59,130,246,.06) 1px, transparent 1px);

          background-size: 40px 40px;

          animation: apexiveGrid 12s linear infinite;

        }

        .apexive-shimmer {
        background: linear-gradient(

            90deg,

            rgba(255,255,255,0),

            rgba(255,255,255,.8),

            rgba(255,255,255,0)

          );

          background-size: 200% 100%;

          animation: apexiveShimmer 3.5s linear infinite;

        }

        .apexive-blink {

          animation: apexiveBlink 2s ease-in-out infinite;

        }

        .apexive-glass {

          background: rgba(255,255,255,.72);

          backdrop-filter: blur(18px);

          -webkit-backdrop-filter: blur(18px);

        }

        @media (prefers-reduced-motion: reduce) {

          .apexive-float,

          .apexive-float-reverse,

          .apexive-pulse,

          .apexive-scan,

          .apexive-grid,

          .apexive-shimmer,

          .apexive-blink {

            animation: none !important;

          }

        }

      `}</style>

      <SiteHeader />

      {dataErrors.length > 0 && (

        <div

          role="status"

          className="border-b border-amber-400/20 bg-amber-400/10 px-6 py-3 text-center text-sm text-amber-200"

        >

          Some community data could not be loaded ({dataErrors.join(", ")}).
          Check the backend API URL and deployment status.

        </div>

      )}

      {/* ========================================================= */}

      {/* HERO                                                      */}

      {/* ========================================================= */}
      <Reveal direction="up">
        <section className="relative isolate overflow-hidden border-b border-slate-200 bg-white">

          <div className="apexive-grid absolute inset-0 -z-20" />

          <GlowOrb className="apexive-pulse -left-32 top-24 h-96 w-96 bg-blue-300/30" />

          <GlowOrb className="apexive-float right-[-120px] top-20 h-[420px] w-[420px] bg-indigo-300/30" />

          <GlowOrb className="apexive-float-reverse bottom-[-160px] left-1/3 h-96 w-96 bg-cyan-200/25" />

          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-500/60 to-transparent" />

          <div className="mx-auto max-w-7xl px-6 py-20 lg:px-8 lg:py-28">

            <div className="grid items-center gap-14 lg:grid-cols-[1.1fr_.9fr]">

              {/* LEFT */}

              <div className="relative">

                <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-blue-200 bg-white/80 px-4 py-2 text-sm font-semibold text-blue-700 shadow-sm backdrop-blur">

                  <span className="relative flex h-2.5 w-2.5">

                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />

                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />

                  </span>

                  Apexive Community

                  <span className="text-slate-400">•</span>

                  AI-Powered Community

                </div>

                <h1 className="max-w-4xl text-5xl font-black tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">

                  Build.

                  <span className="text-blue-600"> Share.</span>

                  <br />

                  <span className="bg-gradient-to-r from-slate-950 via-blue-700 to-indigo-600 bg-clip-text text-transparent">

                    Learn.

                  </span>

                </h1>

                <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-600">

                  A technical community for developers, engineers, builders,

                  researchers, and technology professionals to discuss ideas,

                  publish knowledge, build projects, and share useful resources.

                </p>

                <div className="mt-9 flex flex-wrap gap-4">

                  <Link

                    href="/forums"

                    className="group relative overflow-hidden rounded-xl bg-slate-950 px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-slate-950/10 transition duration-300 hover:-translate-y-1 hover:bg-blue-700 hover:shadow-blue-500/25"

                  >

                    <span className="relative z-10">Explore Forums →</span>

                    <span className="apexive-shimmer absolute inset-0" />

                  </Link>

                  <Link

                    href="/articles"

                    className="rounded-xl border border-slate-300 bg-white/80 px-6 py-3.
                  5 text-sm font-bold text-slate-700 shadow-sm backdrop-blur transition duration-300 hover:-translate-y-1 hover:border-blue-300 hover:text-blue-600 hover:shadow-lg"

                  >

                    Read Articles

                  </Link>

                  <Link

                    href="/projects"

                    className="rounded-xl border border-slate-300 bg-white/80 px-6 py-3.5 text-sm font-bold text-slate-700 shadow-sm backdrop-blur transition duration-300 hover:-translate-y-1 hover:border-blue-300 hover:text-blue-600 hover:shadow-lg"

                  >

                    Explore Projects

                  </Link>

                </div>

              </div>

              {/* RIGHT — ANIMATED SYSTEM CARD */}

              <div className="relative mx-auto w-full max-w-xl">

                <div className="apexive-float relative rounded-[28px] border border-slate-200 bg-slate-950 p-2 shadow-2xl shadow-blue-900/20">

                  <div className="relative overflow-hidden rounded-[22px] border border-slate-800 bg-[#080d18] p-6">

                    <div className="absolute inset-0 opacity-50">

                      <div className="apexive-grid h-full w-full [background-image:linear-gradient(rgba(96,165,250,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(96,165,250,.08)_1px,transparent_1px)]" />

                    </div>

                    <div className="relative">

                      <div className="flex items-center justify-between">

                        <div>

                          <p className="text-xs font-bold uppercase tracking-[.25em] text-blue-400">

                            APEXIVE SYSTEM

                          </p>

                          <p className="mt-1 text-sm text-slate-400">

                            Community Intelligence

                          </p>

                        </div>

                        <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5">

                          <span className="apexive-blink h-2 w-2 rounded-full bg-emerald-400" />

                          <span className="text-xs font-bold text-emerald-400">

                            ONLINE

                          </span>

                        </div>

                      </div>

                      <div className="mt-8 grid grid-cols-2 gap-3">

                        {[

                          ["COMMUNITY", "ACTIVE"],

                          ["KNOWLEDGE", "READY"],

                          ["PROJECTS", "LIVE"],

                          ["AI ENGINE", "ONLINE"],

                        ].map(([label, value]) => (

                          <div

                            key={label}

                            className="rounded-2xl border border-slate-800 bg-white/[.04] p-4 transition duration-300 hover:border-blue-500/40 hover:bg-blue-500/[.06]"

                          >

                            <p className="text-[10px] font-bold tracking-widest text-slate-500">

                              {label}

                            </p>

                            <p className="mt-2 text-sm font-bold text-white">

                              {value}

                            </p>

                          </div>

                        ))}

                      </div>

                      <div className="mt-5 rounded-2xl border border-blue-500/20 bg-blue-500/[.05] p-5">

                        <div className="flex items-center justify-between">

                          <span className="text-xs font-bold text-slate-400">

                            INTELLIGENCE STREAM

                          </span>

                          <span className="text-xs text-blue-400">

                            LIVE

                          </span>

                        </div>

                        <div className="mt-5 flex h-20 items-end gap-1.5">

                          {[30, 46, 38, 62, 48, 76, 56, 82, 68, 91, 72, 96, 80, 100].map(

                            (height, index) => (

                              <div

                                key={index}
                                className="flex-1 rounded-t bg-gradient-to-t from-blue-700 to-cyan-300 opacity-80 transition-all duration-500 hover:opacity-100"

                                style={{

                                  height: `${height}%`,

                                  animationDelay: `${index * 80}ms`,

                                }}

                              />

                            )

                          )}

                        </div>

                      </div>

                      <div className="relative mt-5 overflow-hidden rounded-xl border border-slate-800 bg-black/20 px-4 py-3">

                        <div className="apexive-scan absolute inset-x-0 top-0 h-px bg-blue-400 shadow-[0_0_15px_#60a5fa]" />

                        <div className="flex items-center gap-3">

                          <span className="h-2 w-2 rounded-full bg-blue-400" />

                          <span className="font-mono text-xs text-slate-400">

                            system://community/stream

                          </span>

                          <span className="ml-auto font-mono text-xs text-emerald-400">

                            READY

                          </span>

                        </div>

                      </div>

                    </div>

                  </div>

                </div>

                <div className="absolute -bottom-6 -left-6 hidden rounded-2xl border border-white bg-white/90 px-5 py-4 shadow-xl backdrop-blur sm:block">

                  <div className="flex items-center gap-3">

                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">

                      ✦

                    </div>

                    <div>

                      <p className="text-xs font-bold text-slate-400">

                        PLATFORM

                      </p>

                      <p className="text-sm font-black text-slate-900">

                        Enterprise Ready

                      </p>

                    </div>

                  </div>

                </div>

              </div>

            </div>

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* STATS                                                     */}

      {/* ========================================================= */}

      <Reveal direction="up">
        <section className="relative border-b border-slate-200 bg-white">

          <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x divide-y divide-slate-200 sm:grid-cols-4 sm:divide-y-0">

            {[

              [latestThreads.length, "Latest Discussions"],

              [articles.length, "Featured Articles"],

              [projects.length, "Featured Projects"],

              [resources.length, "Featured Resources"],

            ].map(([value, label], index) => (

              <div

                key={String(label)}

                className="group relative overflow-hidden px-6 py-9 text-center transition duration-300 hover:bg-blue-50/40"

              >

                <div className="absolute inset-x-0 bottom-0 h-0.5 origin-left scale-x-0 bg-blue-500 transition duration-500 group-hover:scale-x-100" />

                <div className="text-4xl font-black tracking-tight text-slate-950 transition duration-300 group-hover:-translate-y-1 group-hover:text-blue-600">

                  {value}

                </div>

                <div className="mt-2 text-xs font-bold uppercase tracking-wider text-slate-500">

                  {label}

                </div>

                <div className="mt-3 text-[10px] font-semibold text-slate-300">

                  0{index + 1} / COMMUNITY

                </div>

              </div>

            ))}

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* PHASE 1                                                   */}

      {/* ========================================================= */}

      <Reveal direction="right">
        <section className="relative overflow-hidden border-b border-slate-200 bg-slate-50">

          <GlowOrb className="apexive-pulse right-[-150px] top-[-100px] h-96 w-96 bg-blue-200/30" />

          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

            <div className="flex items-end justify-between gap-4">

              <div>

                <p className="text-sm font-bold uppercase tracking-[.18em] text-blue-600">

                  Enterprise Platform

                </p>

                <h2 className="mt-2 text-3xl font-black text-slate-950">

                  Phase 1

                </h2>

                <p className="mt-2 max-w-2xl text-slate-600">

                  Governed enterprise capabilities for legal operations,

                  document workflows, knowledge retrieval, approvals,

                  integrations, and auditability.

                </p>

              </div>

              <Link

                href="/phase-1"

                className="hidden rounded-lg px-3 py-2 text-sm font-bold text-blue-600 transition hover:bg-blue-50 sm:block"

              >

                View More →

              </Link>

            </div>

            <div className="mt-8">

              <Link

                href="/phase-1"

                className="group relative block overflow-hidden rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition duration-500 hover:-translate-y-2 hover:border-blue-300 hover:shadow-2xl hover:shadow-blue-900/10"

              >

                <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-blue-100/50 blur-3xl transition duration-700 group-hover:scale-150" />

                <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">

                  <div className="flex items-start gap-5">

                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 text-3xl shadow-inner transition duration-500 group-hover:rotate-6 group-hover:scale-110">

                      ⚖

                    </div>

                    <div>

                      <div className="flex flex-wrap items-center gap-3">

                        <h3 className="text-xl font-black text-[#172033]">

                          Enterprise Legal Operations

                        </h3>

                        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">

                          Phase 1

                        </span>

                      </div>

                      <p className="mt-2 text-sm font-semibold text-slate-500">

                        Governed AI capabilities

                      </p>

                      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">

                        Legal knowledge, RFP analysis, RFI generation,

                        contract drafting, precedent retrieval, document

                        comparison, SharePoint and Teams integration,

                        human approval workflows, audit logs, and access

                        control.

                      </p>

                      <div className="mt-4 flex flex-wrap gap-2">

                        {[

                          "Legal Knowledge",

                          "RFP Analysis",

                          "RFI",

                          "Contract Drafting",

                          "SharePoint",

                          "Microsoft Teams",

                          "Human Approval",

                          "Audit Log",

                        ].map((item) => (

                          <span

                            key={item}

                            className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600 transition group-hover:bg-blue-50 group-hover:text-blue-700"

                          >

                            {item}

                          </span>

                        ))}

                      </div>

                    </div>

                  </div>
                  <div className="flex shrink-0 items-center gap-2 text-sm font-black text-blue-600 transition duration-300 group-hover:translate-x-2">

                    View More

                    <span className="text-lg">→</span>

                  </div>

                </div>

              </Link>

            </div>

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* DISCUSSIONS                                               */}

      {/* ========================================================= */}
      <Reveal direction="up">
        <section className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

          <div className="flex items-end justify-between gap-4">

            <div>

              <p className="text-sm font-bold uppercase tracking-[.18em] text-blue-600">

                Community

              </p>

              <h2 className="mt-2 text-3xl font-black text-slate-950">

                Popular Discussions

              </h2>

              <p className="mt-2 text-slate-600">

                Join conversations happening across the community.

              </p>

            </div>

            <Link

              href="/forums"

              className="hidden rounded-lg px-3 py-2 text-sm font-bold text-blue-600 transition hover:bg-blue-50 sm:block"

            >

              View all →

            </Link>

          </div>

          <div className="mt-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">

            {latestThreads.length === 0 ? (

              <div className="p-10 text-center text-slate-500">

                No discussions available yet.

              </div>

            ) : (

              latestThreads.map((thread, index) => (

                <Link

                  key={thread.id}

                  href={`/forums/${thread.slug}`}

                  className="group relative block border-b border-slate-100 p-6 transition duration-300 last:border-b-0 hover:bg-slate-50"

                >

                  <div className="absolute bottom-0 left-0 top-0 w-1 origin-bottom scale-y-0 bg-blue-600 transition duration-300 group-hover:scale-y-100" />

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

                    <div className="flex min-w-0 items-start gap-4">

                      <span className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-xs font-black text-slate-500 sm:flex group-hover:bg-blue-50 group-hover:text-blue-600">

                        {String(index + 1).padStart(2, "0")}

                      </span>

                      <div className="min-w-0">

                        <h3 className="truncate text-lg font-bold text-slate-900 transition group-hover:text-blue-600">

                          {thread.title}

                        </h3>

                        <p className="mt-1 line-clamp-2 text-sm text-slate-500">

                          {thread.content}

                        </p>

                      </div>

                    </div>

                    <div className="shrink-0 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-400 transition group-hover:bg-blue-50 group-hover:text-blue-600">

                      {thread.views} views

                    </div>

                  </div>

                </Link>

              ))

            )}

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* ARTICLES                                                  */}

      {/* ========================================================= */}
      <Reveal direction="left">
        <section className="border-y border-slate-200 bg-slate-50">

          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

            <div className="flex items-end justify-between gap-4">

              <div>

                <p className="text-sm font-bold uppercase tracking-[.18em] text-blue-600">

                  Knowledge

                </p>

                <h2 className="mt-2 text-3xl font-black text-slate-950">

                  Featured Articles

                </h2>
                <p className="mt-2 text-slate-600">

                  Technical knowledge from builders in the community.

                </p>

              </div>

              <Link

                href="/articles"

                className="hidden rounded-lg px-3 py-2 text-sm font-bold text-blue-600 transition hover:bg-blue-100 sm:block"

              >

                View all →

              </Link>

            </div>

            {featuredArticles.length === 0 ? (

              <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">

                No featured articles available yet.

              </div>

            ) : (

              <div className="mt-8 grid gap-6 md:grid-cols-3">

                {featuredArticles.map((article: Article, index) => (

                  <Link

                    key={article.id}

                    href={`/articles/${article.slug}`}

                    className="group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition duration-500 hover:-translate-y-2 hover:border-blue-200 hover:shadow-2xl hover:shadow-blue-900/10"

                  >

                    <div className="absolute right-[-40px] top-[-40px] h-32 w-32 rounded-full bg-blue-100/50 blur-2xl transition duration-700 group-hover:scale-150" />

                    <div className="relative flex items-center justify-between gap-3">

                      <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">

                        {article.category}

                      </span>

                      <span className="text-xs font-bold text-slate-400">

                        {article.read_time_minutes} min

                      </span>

                    </div>

                    <div className="relative mt-5 text-[10px] font-black uppercase tracking-widest text-slate-300">

                      ARTICLE 0{index + 1}

                    </div>

                    <h3 className="relative mt-2 text-xl font-black text-slate-950 transition group-hover:text-blue-600">

                      {article.title}

                    </h3>

                    <p className="relative mt-3 line-clamp-3 text-sm leading-6 text-slate-600">

                      {article.excerpt}

                    </p>

                    <div className="relative mt-6 flex items-center justify-between border-t border-slate-100 pt-5 text-xs text-slate-400">

                      <span>{formatDate(article.created_at)}</span>

                      <span>{article.views} views</span>

                    </div>

                  </Link>

                ))}

              </div>

            )}

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* PROJECTS                                                  */}

      {/* ========================================================= */}
      <Reveal direction="right">
        <section className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

          <div className="flex items-end justify-between gap-4">

            <div>

              <p className="text-sm font-bold uppercase tracking-[.18em] text-blue-600">

                Building

              </p>

              <h2 className="mt-2 text-3xl font-black text-slate-950">

                Featured Projects

              </h2>

              <p className="mt-2 text-slate-600">

                Discover projects being built by the community.

              </p>

            </div>

            <Link

              href="/projects"

              className="hidden rounded-lg px-3 py-2 text-sm font-bold text-blue-600 transition hover:bg-blue-50 sm:block"

            >

              View all →

            </Link>

          </div>

          {featuredProjects.length === 0 ? (

            <div className="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-10 text-center text-slate-500">

              No featured projects available yet.

            </div>

          ) : (

            <div className="mt-8 grid gap-6 md:grid-cols-3">

              {featuredProjects.map((project: Project, index) => (

                <Link
                  key={project.id}

                  href={`/projects/${project.slug}`}

                  className="group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition duration-500 hover:-translate-y-2 hover:border-blue-200 hover:shadow-2xl hover:shadow-blue-900/10"

                >

                  <div className="absolute inset-x-0 top-0 h-1 origin-left scale-x-0 bg-gradient-to-r from-blue-500 to-indigo-500 transition duration-500 group-hover:scale-x-100" />

                  <div className="flex items-center justify-between">

                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 transition group-hover:bg-blue-50 group-hover:text-blue-700">

                      {project.category}

                    </span>

                    <span className="text-xs font-bold text-emerald-600">

                      {project.status}

                    </span>

                  </div>

                  <div className="mt-6 text-[10px] font-black uppercase tracking-widest text-slate-300">

                    PROJECT 0{index + 1}

                  </div>

                  <h3 className="mt-2 text-xl font-black text-slate-950 transition group-hover:text-blue-600">

                    {project.name}

                  </h3>

                  <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">

                    {project.description}

                  </p>

                  <div className="mt-6 flex items-center justify-between text-xs font-semibold text-slate-400">

                    <span>★ {project.stars}</span>

                    <span>{project.views} views</span>

                  </div>

                </Link>

              ))}

            </div>

          )}

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* RESOURCES                                                 */}

      {/* ========================================================= */}

      <Reveal direction="left">
        <section className="border-y border-slate-200 bg-slate-50">

          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

            <div className="flex items-end justify-between gap-4">

              <div>

                <p className="text-sm font-bold uppercase tracking-[.18em] text-blue-600">

                  Library

                </p>

                <h2 className="mt-2 text-3xl font-black text-slate-950">

                  Latest Resources

                </h2>

                <p className="mt-2 text-slate-600">

                  Guides, documents, tools, and useful technical material.

                </p>

              </div>

              <Link

                href="/resources"

                className="hidden rounded-lg px-3 py-2 text-sm font-bold text-blue-600 transition hover:bg-blue-100 sm:block"

              >

                View all →

              </Link>

            </div>

            {latestResources.length === 0 ? (

              <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">

                No resources available yet.

              </div>

            ) : (

              <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                {latestResources.map((resource: Resource) => (

                  <Link

                    key={resource.id}

                    href={`/resources/${resource.slug}`}

                    className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-500 hover:-translate-y-2 hover:border-blue-200 hover:shadow-xl"

                  >

                    <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-blue-100/40 blur-2xl transition duration-500 group-hover:scale-150" />

                    <div className="relative text-xs font-black uppercase tracking-wide text-blue-600">

                      {resource.resource_type}

                    </div>

                    <h3 className="relative mt-3 line-clamp-2 font-black text-slate-950 transition group-hover:text-blue-600">

                      {resource.title}

                    </h3>

                    <p className="relative mt-2 line-clamp-3 text-sm leading-6 text-slate-600">

                      {resource.description}

                    </p>

                    <div className="relative mt-5 flex items-center justify-between border-t border-slate-100 pt-4 text-xs text-slate-400">

                      <span>{resource.category}</span>

                      <span>{resource.downloads} downloads</span>

                    </div>

                  </Link>

                ))}

              </div>

            )}

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* CTA                                                       */}

      {/* ========================================================= */}

      <Reveal direction="scale">
        <section className="relative overflow-hidden bg-[#070b14]">

          <div className="apexive-grid absolute inset-0 opacity-30" />

          <GlowOrb className="apexive-pulse left-1/4 top-[-160px] h-96 w-96 bg-blue-600/20" />

          <GlowOrb className="apexive-float right-[-100px] bottom-[-160px] h-96 w-96 bg-indigo-600/20" />

          <div className="relative mx-auto max-w-7xl px-6 py-24 text-center lg:px-8">

            <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-400/10 px-4 py-2 text-xs font-bold uppercase tracking-widest text-blue-300">

              <span className="apexive-blink h-2 w-2 rounded-full bg-blue-400" />

              Community Intelligence

            </div>

            <h2 className="text-4xl font-black tracking-tight text-white sm:text-5xl">

              Build something

              <span className="text-blue-400"> worth sharing.</span>

            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-slate-400">

              Start a discussion, publish an article, share a project, or

              contribute a useful resource to the Apexive Community.

            </p>

            <div className="mt-9 flex flex-wrap justify-center gap-4">

              <Link

                href="/forums/new"

                className="rounded-xl bg-white px-6 py-3.5 text-sm font-black text-slate-950 shadow-lg transition duration-300 hover:-translate-y-1 hover:bg-blue-50 hover:shadow-blue-500/20"

              >

                Start a Discussion

              </Link>

              <Link

                href="/projects/new"

                className="rounded-xl border border-slate-700 bg-white/[.03] px-6 py-3.5 text-sm font-black text-white transition duration-300 hover:-translate-y-1 hover:border-blue-500 hover:bg-blue-500/10"

              >

                Submit a Project

              </Link>

            </div>

          </div>

        </section>
      </Reveal>

      {/* ========================================================= */}

      {/* FOOTER                                                    */}

      {/* ========================================================= */}

      <footer className="border-t border-slate-800 bg-[#070b14]">

        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 text-sm text-slate-400 lg:px-8">

          <div className="flex flex-col items-center gap-8 sm:flex-row sm:items-center sm:justify-between">

            <Image

              src="/copyright-seal.png"

              alt="Copyright - Bhone Htet Naing"

              width={280}

              height={280}

              className="h-auto w-full max-w-[220px] rounded-xl border border-amber-500/20 object-contain transition duration-500 hover:scale-105"

            />

            <div className="text-center sm:text-left">

              <div className="font-semibold text-slate-300">

                © {new Date().getFullYear()} Apexive Community

              </div>

              <div className="mt-1 text-xs text-slate-600">

                Technical Community & Enterprise Intelligence Platform

              </div>

            </div>

            <div className="flex flex-wrap justify-center gap-5">

              <Link href="/forums" className="transition hover:text-white">

                Forums

              </Link>

              <Link href="/articles" className="transition hover:text-white">

                Articles

              </Link>

              <Link href="/projects" className="transition hover:text-white">

                Projects

              </Link>

              <Link href="/resources" className="transition hover:text-white">

                Resources

              </Link>

            </div>

          </div>

        </div>

      </footer>

    </div>

  );

}