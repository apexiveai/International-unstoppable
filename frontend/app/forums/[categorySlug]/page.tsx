"use client";

import Link from "next/link";

import { use, useEffect, useState } from "react";
import API_URL from "@/lib/api";

type Category = {

  id: number;

  name: string;

  slug: string;

  description: string;

};

const telecomSections = [
  ["Core Network", ["EPC / 4G Core", "5G Core", "IMS", "Signaling"]],
  ["Radio Access Network", ["2G / GSM", "3G / UMTS", "4G / LTE", "5G / NR"]],
  ["IP & Transport", ["IP Networking", "MPLS", "Microwave", "Fiber", "SDN / SD-WAN"]],
  ["Network Operations", ["NOC", "Monitoring", "Troubleshooting", "Performance", "Network Automation"]],
  ["Telecom Security", ["Network Security", "Signaling Security", "4G / 5G Security", "Fraud & Abuse"]],
  ["Telecom Power", ["Rectifier", "Battery", "Generator", "Solar", "Site Power"]],
] as const;

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

export default function CategoryPage({

  params,

}: {
  params: Promise<{ categorySlug: string }>;
}) {
  const { categorySlug } = use(params);
  const [category, setCategory] =

    useState<Category | null>(null);

  const [threads, setThreads] =

    useState<Thread[]>([]);

  const [filter, setFilter] =

    useState<"all" | "question" | "discussion">(

      "all"

    );

  const [loading, setLoading] = useState(true);

  useEffect(() => {

    async function load() {

      try {

        const categoryResponse = await fetch(

          `${API_URL}/api/categories/${encodeURIComponent(categorySlug)}`

        );

        if (!categoryResponse.ok) {

          throw new Error("Category not found");

        }

        const categoryData =

          await categoryResponse.json();

        setCategory(categoryData);

        const threadResponse = await fetch(
          `${API_URL}/api/threads?category_id=${categoryData.id}`

        );

        if (!threadResponse.ok) {

          throw new Error("Failed to load discussions");

        }

        setThreads(await threadResponse.json());

      } catch (error) {

        console.error(error);

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [categorySlug, filter]);

  if (loading) {

    return (

      <main className="min-h-screen bg-slate-950 p-10 text-slate-400">

        Loading...

      </main>

    );

  }

  if (!category) {

    return (

      <main className="min-h-screen bg-slate-950 p-10 text-white">

        Forum not found.

      </main>

    );

  }

  return (

    <main className="min-h-screen bg-slate-950 text-white">

      <div className="mx-auto max-w-6xl px-6 py-10">

        <Link

          href="/forums"

          className="text-sm text-slate-500 hover:text-emerald-400"

        >

          ← Forums

        </Link>

        <div className="mt-6 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">

          <div>

            <h1 className="text-4xl font-bold">

              {category.name}

            </h1>

            <p className="mt-3 max-w-3xl text-slate-400">

              {category.description}

            </p>

          </div>

          <Link

            href={`/forums/${category.slug}/new`}

            className="rounded-xl bg-emerald-500 px-5 py-3 text-center font-semibold text-slate-950 transition hover:bg-emerald-400"

          >

            + New Discussion

          </Link>

        </div>

        <div className="mt-8 flex gap-2">

          {[

            ["all", "All"],

            ["question", "Questions & Answers"],

            ["discussion", "Discussions"],

          ].map(([value, label]) => (

            <button

              key={value}

              onClick={() =>

                setFilter(

                  value as

                    | "all"

                    | "question"

                    | "discussion"

                )

              }

              className={`rounded-lg px-4 py-2 text-sm ${

                filter === value

                  ? "bg-emerald-500 text-slate-950"

                  : "bg-slate-900 text-slate-400 hover:text-white"

              }`}

            >

              {label}

            </button>

          ))}

        </div>

        <div className="mt-6 overflow-hidden rounded-2xl border border-slate-800">

          {threads.length === 0 ? (
<div className="p-10 text-center text-slate-500">

              No discussions yet.

            </div>

          ) : (

            threads.map((thread) => (

              <Link

                key={thread.id}

                href={`/forums/${category.slug}/${thread.slug}`}

                className="block border-b border-slate-800 bg-slate-900/60 p-6 last:border-b-0 hover:bg-slate-900"

              >

                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                  <div className="min-w-0">

                    <div className="mb-2 flex flex-wrap gap-2">

                      <span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-400">
                        Discussion

                      </span>

                    </div>

                    <h2 className="truncate text-lg font-semibold">

                      {thread.title}

                    </h2>

                    <p className="mt-2 line-clamp-2 text-sm text-slate-500">

                      {thread.content}

                    </p>

                  </div>

                  <div className="shrink-0 text-sm text-slate-500">

                    {thread.views} views

                  </div>

                  {category.slug === "telecom-networking" && (
                    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
                      <h2 className="text-xl font-semibold">Telecom &amp; Networking Topics</h2>
                      <div className="mt-6 grid gap-4 md:grid-cols-2">
                        {telecomSections.map(([section, topics]) => (
                          <div key={section} className="rounded-xl border border-slate-800 bg-slate-950 p-5">
                            <h3 className="font-semibold text-emerald-400">{section}</h3>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {topics.map((topic) => (
                                <span key={topic} className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                </div>

              </Link>

            ))

          )}

        </div>

      </div>

    </main>

  );

}