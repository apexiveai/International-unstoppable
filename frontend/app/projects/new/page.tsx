"use client";

import { FormEvent, useState } from "react";

import { useRouter } from "next/navigation";

import Link from "next/link";
import RequireAuth from "@/components/RequireAuth";
import SiteHeader from "@/components/SiteHeader";

import { createProject } from "@/lib/api";

export default function NewProjectPage() {

  const router = useRouter();

  const [name, setName] = useState("");

  const [slug, setSlug] = useState("");

  const [description, setDescription] = useState("");

  const [content, setContent] = useState("");

  const [category, setCategory] = useState("");

  const [repositoryUrl, setRepositoryUrl] = useState("");

  const [websiteUrl, setWebsiteUrl] = useState("");

  const [status, setStatus] = useState("Building");

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

  function handleNameChange(value: string) {

    setName(value);

    if (!slug) {

      setSlug(generateSlug(value));

    }

  }
  
  async function handleSubmit(event: FormEvent) {

    event.preventDefault();

    setError("");

    setLoading(true);

    try {

      await createProject({

        name,

        slug,

        description,

        content,

        category,

        repository_url: repositoryUrl || null,

        website_url: websiteUrl || null,

        status,

        is_featured: false,

      });

      router.push(`/projects/${slug}`);

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Failed to create project",

      );

    } finally {

      setLoading(false);

    }

  }

  return (
    <RequireAuth nextPath="/projects/new">
      <div className="min-h-screen bg-slate-50">

      <SiteHeader />

      <main className="mx-auto max-w-4xl px-6 py-12 lg:px-8">

        <Link

          href="/projects"

          className="text-sm font-medium text-blue-600"

        >

          ← Back to Projects

        </Link>

        <h1 className="mt-4 text-3xl font-bold text-slate-950">

          Submit a Project

        </h1>

        <p className="mt-2 text-slate-600">

          Showcase something you are building.

        </p>

        <form

          onSubmit={handleSubmit}

          className="mt-8 space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"

        >

          {error && (

            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">

              {error}

            </div>

          )}

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Project Name

            </label>

            <input

              value={name}

              onChange={(e) => handleNameChange(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="My AI Platform"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Slug

            </label>

            <input

              value={slug}

              onChange={(e) => setSlug(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="my-ai-platform"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Category

            </label>

            <input

              value={category}

              onChange={(e) => setCategory(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="AI / Web / Hardware"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Description

            </label>

            <textarea

              value={description}
              onChange={(e) => setDescription(e.target.value)}

              required

              rows={4}

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Project Details

            </label>

            <textarea

              value={content}

              onChange={(e) => setContent(e.target.value)}

              rows={12}

              className="w-full rounded-xl border border-slate-300 px-4 py-3 font-mono text-sm"

              placeholder="Explain the project, architecture, technologies, roadmap..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Repository URL

            </label>

            <input

              value={repositoryUrl}

              onChange={(e) => setRepositoryUrl(e.target.value)}

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="https://github.com/..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Website URL

            </label>

            <input

              value={websiteUrl}

              onChange={(e) => setWebsiteUrl(e.target.value)}

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="https://..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              Status

            </label>

            <select

              value={status}

              onChange={(e) => setStatus(e.target.value)}

              className="rounded-xl border border-slate-300 px-4 py-3"

            >

              <option>Building</option>

              <option>Active</option>

              <option>Completed</option>

              <option>Paused</option>

              <option>Archived</option>

            </select>

          </div>

          <div className="border-t border-slate-200 pt-6">

            <button

              type="submit"

              disabled={loading}

              className="rounded-xl bg-slate-950 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"

            >

              {loading ? "Submitting..." : "Submit Project"}

            </button>

          </div>

        </form>

      </main>

      </div>
    </RequireAuth>
  );

}