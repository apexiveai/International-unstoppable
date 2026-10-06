"use client";

import Link from "next/link";

import { useEffect, useState } from "react";
import API_URL from "@/lib/api";

type Category = {

  id: number;

  name: string;

  slug: string;

  description: string;

};

const icons: Record<string, string> = {

  security: "🔐",

  "data-cloud": "☁️",

  development: "💻",

  "artificial-intelligence": "🧠",
  "telecom-networking": "📡",
};

export default function ForumsPage() {

  const [categories, setCategories] = useState<Category[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {

    let mounted = true;

    fetch(`${API_URL}/api/categories`)

      .then(async (res) => {
        if (!res.ok) {
          const detail = await res.text();
          throw new Error(
            detail || `Unable to load forums (HTTP ${res.status}).`,
          );
        }
        return res.json();
      })

      .then((result: Category[]) => {
        if (mounted) {
          setCategories(result);
          setError("");
        }
      })

      .catch((reason: unknown) => {
        if (mounted) {
          const detail = reason instanceof Error ? ` ${reason.message}` : "";
          setError(
            `Unable to reach the forums API at ${API_URL}. Check that the backend is online and allows this frontend origin.${detail}`,
          );
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };

  }, [retryCount]);

  return (

    <main className="min-h-screen bg-white text-slate-950">

      <div className="mx-auto max-w-7xl px-6 py-12">

        <div className="mb-10">

          <div className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">

            Community Discussion

          </div>

          <h1 className="text-4xl font-bold tracking-tight">

            Forums

          </h1>

          <p className="mt-3 max-w-3xl text-slate-400">

            Ask questions, start discussions, share solutions,

            and build reusable technology knowledge with the

            Apexive Community.

          </p>

        </div>

        {loading ? (

          <div className="text-slate-400">

            Loading forums...

          </div>

        ) : error ? (
          <div role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-200">
            <p className="font-semibold">Forums are temporarily unavailable.</p>
            <p className="mt-2 text-sm">{error}</p>
            <button
              type="button"
              onClick={() => {
                setError("");
                setLoading(true);
                setRetryCount((count) => count + 1);
              }}
              className="mt-4 rounded-lg border border-rose-300/30 px-4 py-2 text-sm font-semibold hover:bg-rose-500/10"
            >
              Try again
            </button>
          </div>
        ) : (

          <div className="grid gap-5 md:grid-cols-2">

            {categories.map((category) => (

              <Link

                key={category.id}

                href={`/forums/${category.slug}`}

                className="group rounded-2xl border border-slate-800 bg-slate-900/70 p-7 text-white transition hover:border-emerald-500/50 hover:bg-slate-900"

              >

                <div className="mb-5 flex items-center justify-between">

                  <div className="text-4xl">

                    {icons[category.slug] || "💬"}

                  </div>

                  <div className="text-slate-600 transition group-hover:text-emerald-400">

                    →

                  </div>

                </div>

                <h2 className="text-2xl font-semibold">

                  {category.name}

                </h2>

                <p className="mt-3 leading-7 text-slate-400">

                  {category.description}

                </p>

                <div className="mt-6 flex gap-2 text-xs font-medium">

                  <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">

                    Questions & Answers

                  </span>

                  <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">

                    Discussions

                  </span>

                </div>

              </Link>

            ))}

          </div>

        )}

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-7 text-white">

          <h2 className="text-xl font-semibold">

            Community Knowledge Sharing

          </h2>

          <p className="mt-3 max-w-3xl leading-7 text-slate-400">

            Every question, explanation, solution, and discussion

            can contribute to a growing technical knowledge base

            for the community.

          </p>

        </section>

      </div>

    </main>

  );

}