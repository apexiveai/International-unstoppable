"use client";

import Link from "next/link";

import { useEffect, useMemo, useState } from "react";

import SiteHeader from "@/components/SiteHeader";

import {

  Article,

  getArticles,

} from "@/lib/api";

const categories = [

  "All",

  "Artificial Intelligence",

  "AI Architecture",

  "Development",

  "Database",

  "Security",

];

export default function ArticlesPage() {

  const [articles, setArticles] = useState<Article[]>([]);

  const [search, setSearch] = useState("");

  const [category, setCategory] = useState("All");

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {

    getArticles()

      .then(setArticles)

      .catch(() => {

        setError("Unable to load articles.");

      })

      .finally(() => {

        setLoading(false);

      });

  }, []);

  const filteredArticles = useMemo(() => {

    const query = search.trim().toLowerCase();

    return articles.filter((article) => {

      const matchesCategory =

        category === "All" ||

        article.category === category;

      const matchesSearch =

        !query ||

        article.title.toLowerCase().includes(query) ||

        article.excerpt.toLowerCase().includes(query) ||

        article.content.toLowerCase().includes(query);

      return matchesCategory && matchesSearch;

    });

  }, [articles, search, category]);

  const featured = articles.find(

    (article) => article.is_featured,

  );

  return (

    <div className="min-h-screen bg-white text-slate-900">

      <SiteHeader />

      <main className="mx-auto max-w-7xl px-6 py-12">

        <div className="max-w-3xl">

          <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">

            Knowledge

          </p>

          <h1 className="mt-3 text-4xl font-black tracking-tight text-[#172033]">

            Articles

          </h1>

          <p className="mt-4 text-slate-500">

            Long-form knowledge, architecture ideas and technical insights
            from the Apexive Community.

          </p>

        </div>

        <div className="mt-8 flex flex-col gap-3 lg:flex-row">

          <input

            value={search}

            onChange={(event) =>

              setSearch(event.target.value)

            }

            placeholder="Search articles..."

            className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

          />

          <Link

            href="/articles/new"

            className="rounded-xl bg-[#172033] px-5 py-3 text-center text-sm font-bold text-white hover:bg-blue-600"

          >

            Write an article

          </Link>

        </div>

        <div className="mt-6 flex flex-wrap gap-2">

          {categories.map((item) => (

            <button

              key={item}

              type="button"

              onClick={() => setCategory(item)}

              className={`rounded-full px-4 py-2 text-xs font-bold transition ${

                category === item

                  ? "bg-[#172033] text-white"

                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"

              }`}

            >

              {item}

            </button>

          ))}

        </div>

        {loading && (

          <div className="py-20 text-center text-sm text-slate-500">

            Loading articles...

          </div>

        )}

        {error && !loading && (

          <div className="mt-10 rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-600">

            {error}

          </div>

        )}

        {!loading && !error && featured && (

          <section className="mt-12 overflow-hidden rounded-3xl bg-[#172033]">

            <div className="max-w-4xl px-8 py-12 sm:px-12">

              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-blue-300">

                Featured Article

              </span>
<div className="mt-5 text-xs font-bold text-slate-400">

                {featured.category}

              </div>

              <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">

                {featured.title}

              </h2>

              <p className="mt-4 max-w-2xl leading-7 text-slate-300">

                {featured.excerpt}

              </p>

              <Link

                href={`/articles/${featured.slug}`}

                className="mt-7 inline-flex rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#172033] hover:bg-blue-50"

              >

                Read article →

              </Link>

            </div>

          </section>

        )}

        {!loading && !error && (

          <section className="mt-12">

            <div className="mb-6 flex items-center justify-between">

              <h2 className="text-2xl font-black text-[#172033]">

                All Articles

              </h2>

              <span className="text-sm text-slate-400">

                {filteredArticles.length} articles

              </span>

            </div>

            {filteredArticles.length === 0 ? (

              <div className="rounded-2xl border border-slate-200 p-12 text-center">

                <h3 className="font-bold text-[#172033]">

                  No articles found

                </h3>

                <p className="mt-2 text-sm text-slate-500">

                  Try another search or category.

                </p>

              </div>

            ) : (

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">

                {filteredArticles.map((article) => (

                  <Link

                    key={article.id}

                    href={`/articles/${article.slug}`}

                    className="group rounded-2xl border border-slate-200 p-6 transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"

                  >

                    <div className="text-xs font-bold text-blue-600">

                      {article.category}

                    </div>

                    <h3 className="mt-4 text-xl font-black tracking-tight text-[#172033] group-hover:text-blue-600">

                      {article.title}

                    </h3>

                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500">

                      {article.excerpt}

                    </p>

                    <div className="mt-6 flex justify-between text-xs text-slate-400">

                      <span>

                        {article.read_time_minutes} min read

                      </span>

                      <span>

                        {article.views} views

                      </span>

                    </div>

                  </Link>

                ))}

              </div>

            )}

          </section>

        )}

      </main>

    </div>

  );

}