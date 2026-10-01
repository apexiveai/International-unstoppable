"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import SiteHeader from "@/components/SiteHeader";
import API_URL from "@/lib/api";

type SearchResult = {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  technologies: string[];
  semantic_score: number;
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [technology, setTechnology] = useState("");
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  async function searchProjects(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setSearched(true);
    setError("");
    const params = new URLSearchParams({ q: query });
    if (technology) params.set("technology", technology);
    if (category) params.set("category", category);
    try {
      const response = await fetch(`${API_URL}/api/search/projects?${params}`);
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail ?? `Search failed (${response.status}).`);
      }
      setResults(await response.json());
    } catch (reason) {
      setResults([]);
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to connect to project search.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-6 py-20">
        <p className="text-xs font-black uppercase tracking-[0.16em] text-blue-600">
          Discover
        </p>
        <h1 className="mt-3 text-4xl font-black tracking-tight text-[#172033]">
          AI Search
        </h1>
        <p className="mt-4 max-w-2xl text-slate-500">
          Projects → Technology → Category → Semantic Ranking
        </p>

        <form onSubmit={searchProjects} className="mt-10 grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search projects, e.g. AI agents"
            className="rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <input
            value={technology}
            onChange={(event) => setTechnology(event.target.value)}
            placeholder="Technology: Python"
            className="rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <input
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            placeholder="Category: AI"
            className="rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <button type="submit" className="rounded-xl bg-[#172033] px-6 py-3 text-sm font-bold text-white hover:bg-blue-600">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {error && (
          <p role="alert" className="mt-8 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </p>
        )}

        {searched && !loading && !error && (
          <section className="mt-10">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-black text-[#172033]">Projects</h2>
              <span className="text-sm text-slate-400">
                Semantic ranking · {results.length} results
              </span>
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              {results.map((project) => (
                <Link key={project.id} href={`/projects/${project.slug}`} className="rounded-2xl border border-slate-200 p-6 transition hover:border-blue-300 hover:shadow-lg">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-blue-600">{project.category}</span>
                    <span className="text-slate-400">{Math.round(project.semantic_score * 100)}% match</span>
                  </div>
                  <h3 className="mt-4 text-xl font-black text-[#172033]">{project.name}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{project.description}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {project.technologies.map((item) => (
                      <span key={item} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{item}</span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
