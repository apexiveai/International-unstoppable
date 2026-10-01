"use client";

import { FormEvent, useState } from "react";

import { useRouter } from "next/navigation";

import Link from "next/link";
import RequireAuth from "@/components/RequireAuth";
import SiteHeader from "@/components/SiteHeader";

import { createArticle } from "@/lib/api";

export default function NewArticlePage() {

  const router = useRouter();

  const [title, setTitle] = useState("");

  const [slug, setSlug] = useState("");

  const [excerpt, setExcerpt] = useState("");

  const [content, setContent] = useState("");

  const [category, setCategory] = useState("");

  const [readTime, setReadTime] = useState(5);

  const [published, setPublished] = useState(true);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  function generateSlug(value: string) {

    return value

      .toLowerCase()

      .trim()

      .replace(/[^a-z0-9\s-]/g, "")

      .replace(/\s+/g, "-")

      .replace(/-+/g, "-");

  }

  function handleTitleChange(value: string) {

    setTitle(value);

    if (!slug) {

      setSlug(generateSlug(value));

    }

  }

  async function handleSubmit(event: FormEvent) {

    event.preventDefault();

    setError("");

    setLoading(true);

    try {

      await createArticle({

        title,

        slug,

        excerpt,

        content,

        category,

        read_time_minutes: readTime,

        is_published: published,

        is_featured: false,

      });

      router.push(`/articles/${slug}`);

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Failed to create article",

      );

    } finally {

      setLoading(false);

    }

  }

  return (
    <RequireAuth nextPath="/articles/new">
        <div className="min-h-screen bg-slate-50">

      <SiteHeader />

      <main className="mx-auto max-w-4xl px-6 py-12 lg:px-8">

        <div className="mb-8">

          <Link

            href="/articles"

            className="text-sm font-medium text-blue-600 hover:text-blue-700"

          >

            ← Back to Articles

          </Link>

          <h1 className="mt-4 text-3xl font-bold text-slate-950">

            Write an Article

          </h1>

          <p className="mt-2 text-slate-600">

            Share technical knowledge with the Apexive Community.

          </p>

        </div>

        <form

          onSubmit={handleSubmit}

          className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"

        >

          {error && (

            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">

              {error}

            </div>

          )}

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Title

            </label>

            <input

              value={title}

              onChange={(e) => handleTitleChange(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

              placeholder="Building Production AI Agents"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Slug

            </label>

            <input

              value={slug}

              onChange={(e) => setSlug(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

              placeholder="building-production-ai-agents"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Category

            </label>

            <input

              value={category}

              onChange={(e) => setCategory(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="AI / Backend / Architecture"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Excerpt

            </label>

            <textarea

              value={excerpt}

              onChange={(e) => setExcerpt(e.target.value)}

              rows={3}

              className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

              placeholder="Short description of the article..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Content

            </label>

            <textarea

              value={content}

              onChange={(e) => setContent(e.target.value)}

              required

              rows={16}

              className="w-full rounded-xl border border-slate-300 px-4 py-3 font-mono text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

              placeholder="Write your article..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">

              Estimated Read Time

            </label>

            <input

              type="number"

              min={1}

              max={120}

              value={readTime}

              onChange={(e) => setReadTime(Number(e.target.value))}

              className="w-40 rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500"

            />

          </div>

          <label className="flex items-center gap-3">

            <input

              type="checkbox"

              checked={published}

              onChange={(e) => setPublished(e.target.checked)}

              className="h-4 w-4"

            />

            <span className="text-sm font-medium text-slate-700">

              Publish immediately

            </span>

          </label>

          <div className="flex gap-3 border-t border-slate-200 pt-6">

            <button

              type="submit"

              disabled={loading}

              className="rounded-xl bg-slate-950 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"

            >

              {loading ? "Publishing..." : "Publish Article"}

            </button>

            <Link

              href="/articles"

              className="rounded-xl border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"

            >

              Cancel

            </Link>

          </div>

        </form>

      </main>

      </div>
    </RequireAuth>
  );

}