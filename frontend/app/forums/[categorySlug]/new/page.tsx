"use client";

import Link from "next/link";

import { use, useEffect, useState } from "react";

import { useRouter } from "next/navigation";
import API_URL from "@/lib/api";

type Category = {

  id: number;

  name: string;

  slug: string;

};

export default function NewThreadPage({

  params,

}: {
  params: Promise<{ categorySlug: string }>;
}) {
  const { categorySlug } = use(params);
  const router = useRouter();

  const [category, setCategory] =

    useState<Category | null>(null);

  const [title, setTitle] =

    useState("");

  const [content, setContent] =
    useState("");
  const [troubleshooting, setTroubleshooting] = useState({
    problem: "",
    network_environment: "",
    symptoms: "",
    logs_alarms: "",
    what_i_tried: "",
  });

  const [threadType, setThreadType] =

    useState<"question" | "discussion">(

      "discussion"

    );

  const [loading, setLoading] =

    useState(false);

  const [error, setError] =

    useState("");

  useEffect(() => {

    const token =

      localStorage.getItem("apexive_token");

    if (!token) {

      router.push(

        `/login?next=/forums/${categorySlug}/new`

      );

      return;

    }

    fetch(

      `${API_URL}/api/categories/${encodeURIComponent(categorySlug)}`

    )

      .then((res) => res.json())

      .then(setCategory)

      .catch(() => {

        setError("Unable to load forum.");

      });

  }, [categorySlug, router]);

  async function submit() {

    setError("");

    if (title.trim().length < 3) {

      setError("Title must be at least 3 characters.");

      return;

    }

    if (!content.trim()) {

      setError("Please write your message.");

      return;

    }

    if (!category) {

      setError("Forum not loaded.");

      return;

    }

    const token =

      localStorage.getItem("apexive_token");

    if (!token) {

      router.push("/login");

      return;

    }

    setLoading(true);

    try {

      const response = await fetch(

        `${API_URL}/api/threads`,

        {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

            Authorization: `Bearer ${token}`,

          },

          body: JSON.stringify({

            title: title.trim(),

            content: content.trim(),

            category_id: category.id,
            ...troubleshooting,

          }),

        }

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail || "Failed to create discussion."

        );

      }

      router.push(

        `/forums/${category.slug}/${data.slug}`

      );

    } catch (error) {

      setError(

        error instanceof Error

          ? error.message

          : "Something went wrong."

      );

    } finally {

      setLoading(false);

    }

  }

  return (

    <main className="min-h-screen bg-slate-950 text-white">

      <div className="mx-auto max-w-4xl px-6 py-10">

        <Link

          href={`/forums/${categorySlug}`}

          className="text-sm text-slate-500 hover:text-emerald-400"

        >

          ← Back to forum

        </Link>

        <h1 className="mt-6 text-3xl font-bold">

          Start a Discussion

        </h1>

        <p className="mt-2 text-slate-400">

          Share a question, technical problem, idea,

          experience, or solution with the community.

        </p>

        <div className="mt-8 space-y-6">

          <div>

            <label className="mb-2 block text-sm font-medium">

              Type

            </label>

            <div className="grid gap-3 sm:grid-cols-2">

              <button

                type="button"

                onClick={() =>

                  setThreadType("question")

                }

                className={`rounded-xl border p-4 text-left ${

                  threadType === "question"

                    ? "border-emerald-500 bg-emerald-500/10"

                    : "border-slate-800 bg-slate-900"

                }`}

              >

                <div className="font-semibold">

                  Questions & Answers

                </div>

                <div className="mt-1 text-sm text-slate-500">
Ask the community for help or a solution.

                </div>

              </button>

              <button

                type="button"

                onClick={() =>

                  setThreadType("discussion")

                }

                className={`rounded-xl border p-4 text-left ${

                  threadType === "discussion"

                    ? "border-emerald-500 bg-emerald-500/10"

                    : "border-slate-800 bg-slate-900"

                }`}

              >

                <div className="font-semibold">

                  Discussion

                </div>

                <div className="mt-1 text-sm text-slate-500">

                  Share ideas, experiences, opinions,

                  or technical knowledge.

                </div>

              </button>

            </div>

          </div>

          {category?.slug === "troubleshooting" && (
            <section className="space-y-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
              <div>
                <h2 className="text-xl font-semibold">Network Troubleshooting</h2>
                <p className="mt-2 text-sm text-slate-400">
                  Provide the incident context so the community can diagnose it systematically.
                </p>
              </div>
              {([
                ["problem", "Problem", "What is failing or what outcome is expected?"],
                ["network_environment", "Network Environment", "Vendor, topology, technology, site, device, and versions."],
                ["symptoms", "Symptoms", "Observed behavior, scope, frequency, and impact."],
                ["logs_alarms", "Logs / Alarms", "Relevant alarm names, timestamps, counters, or sanitized logs."],
                ["what_i_tried", "What I Tried", "Tests, changes, commands, and their results."],
              ] as const).map(([key, label, placeholder]) => (
                <div key={key}>
                  <label className="mb-2 block text-sm font-medium">{label}</label>
                  <textarea
                    value={troubleshooting[key]}
                    onChange={(event) => setTroubleshooting((current) => ({ ...current, [key]: event.target.value }))}
                    rows={3}
                    placeholder={placeholder}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500"
                  />
                </div>
              ))}
            </section>
          )}

          <div>

            <label className="mb-2 block text-sm font-medium">

              Title

            </label>

            <input

              value={title}

              onChange={(e) =>

                setTitle(e.target.value)

              }

              maxLength={300}

              placeholder="What would you like to discuss?"

              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 outline-none focus:border-emerald-500"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-medium">

              Message

            </label>

            <textarea

              value={content}

              onChange={(e) =>

                setContent(e.target.value)

              }

              rows={12}

              maxLength={50000}

              placeholder="Explain your question or discussion..."

              className="w-full resize-y rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 outline-none focus:border-emerald-500"

            />

          </div>

          {error && (

            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">

              {error}

            </div>

          )}

          <button

            type="button"

            onClick={submit}

            disabled={loading}

            className="w-full rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"

          >

            {loading

              ? "Publishing..."

              : "Publish Discussion"}

          </button>

        </div>

      </div>

    </main>

  );

}