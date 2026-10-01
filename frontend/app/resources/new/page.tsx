"use client";

import { FormEvent, useState } from "react";

import { useRouter } from "next/navigation";

import Link from "next/link";
import RequireAuth from "@/components/RequireAuth";
import SiteHeader from "@/components/SiteHeader";

import { createResource } from "@/lib/api";

export default function NewResourcePage() {

  const router = useRouter();

  const [title, setTitle] = useState("");

  const [slug, setSlug] = useState("");

  const [description, setDescription] = useState("");

  const [content, setContent] = useState("");

  const [resourceType, setResourceType] = useState("Guide");

  const [category, setCategory] = useState("");

  const [fileUrl, setFileUrl] = useState("");

  const [fileSize, setFileSize] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const categories = [
    "Documentation",
    "Developer Tools",
    "AI Tools",
    "Security Tools",
    "Cloud Resources",
    "Learning Materials",
    "References",
  ];

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

      await createResource({

        title,

        slug,

        description,

        content,

        resource_type: resourceType,

        category,

        file_url: fileUrl || null,

        file_size: fileSize || null,

        is_featured: false,

        is_published: true,

      });

      router.push(`/resources/${slug}`);

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Failed to create resource",

      );

    } finally {

      setLoading(false);

    }

  }

  return (
    <RequireAuth nextPath="/resources/new">
      <div className="min-h-screen bg-slate-50">

      <SiteHeader />

      <main className="mx-auto max-w-4xl px-6 py-12 lg:px-8">

        <Link

          href="/resources"

          className="text-sm font-medium text-blue-600"

        >

          ← Back to Resources

        </Link>

        <h1 className="mt-4 text-3xl font-bold text-slate-950">

          Submit a Resource

        </h1>

        <p className="mt-2 text-slate-600">

          Share useful technical material with the community.

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

              Title

            </label>

            <input

              value={title}

              onChange={(e) => handleTitleChange(e.target.value)}

              required

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="Production PostgreSQL Checklist"

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

            />

          </div>

          <div className="grid gap-6 sm:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold">

                Resource Type

              </label>

              <select

                value={resourceType}

                onChange={(e) => setResourceType(e.target.value)}

                className="w-full rounded-xl border border-slate-300 px-4 py-3"

              >

                <option>Guide</option>

                <option>Document</option>

                <option>Template</option>

                <option>Tool</option>
                
                <option>Dataset</option>

                <option>Code</option>

                <option>Checklist</option>

              </select>

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold">

                Category

              </label>

              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-300 px-4 py-3"
              >
                <option value="" disabled>
                  Select a category
                </option>
                {categories.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>

            </div>

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

              Content

            </label>

            <textarea

              value={content}

              onChange={(e) => setContent(e.target.value)}

              rows={12}

              className="w-full rounded-xl border border-slate-300 px-4 py-3 font-mono text-sm"

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              File URL

            </label>

            <input

              value={fileUrl}

              onChange={(e) => setFileUrl(e.target.value)}

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="https://..."

            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-semibold">

              File Size

            </label>

            <input

              value={fileSize}

              onChange={(e) => setFileSize(e.target.value)}

              className="w-full rounded-xl border border-slate-300 px-4 py-3"

              placeholder="2.4 MB"

            />

          </div>

          <div className="border-t border-slate-200 pt-6">

            <button

              type="submit"

              disabled={loading}

              className="rounded-xl bg-slate-950 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"

            >

              {loading ? "Submitting..." : "Submit Resource"}

            </button>

          </div>

        </form>

      </main>

      </div>
    </RequireAuth>
  );

}