"use client";

import Link from "next/link";

import { useEffect, useMemo, useState } from "react";

import SiteHeader from "@/components/SiteHeader";

import {

  getResources,

  Resource,

} from "@/lib/api";

const categories = [

  "All",

  "Documentation",

  "Developer Tools",

  "AI Tools",

  "Security Tools",

  "Cloud Resources",

  "Learning Materials",

  "References",

];

const types = [

  "All",

  "PDF",

  "Template",

  "Cheat Sheet",

  "Guide",

  "Repository",

];

export default function ResourcesPage() {

  const [resources, setResources] = useState<Resource[]>([]);

  const [search, setSearch] = useState("");

  const [category, setCategory] = useState("All");

  const [type, setType] = useState("All");

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResources()
      .then(setResources)
      .catch(() => setResources([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {

    const query = search.trim().toLowerCase();

    return resources.filter((resource) => {

      const categoryMatch =

        category === "All" ||

        resource.category === category;

      const typeMatch =

        type === "All" ||

        resource.resource_type === type;

      const searchMatch =

        !query ||

        resource.title.toLowerCase().includes(query) ||

        resource.description

          .toLowerCase()

          .includes(query);

      return (

        categoryMatch &&

        typeMatch &&

        searchMatch

      );

    });

  }, [resources, search, category, type]);

  return (

    <div className="min-h-screen bg-white">

      <SiteHeader />

      <main className="mx-auto max-w-7xl px-6 py-12">

        <div className="flex flex-col gap-6 md:flex-row md:items-end">

          <div className="flex-1">

            <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">

              Knowledge Base

            </p>

            <h1 className="mt-3 text-4xl font-black text-[#172033]">

              Resources

            </h1>

            <p className="mt-4 max-w-2xl text-slate-500">

              Documentation, developer tools, AI tools, security tools,
              cloud resources, learning materials and references shared by
              the community.

            </p>

          </div>

          <Link

            href="/resources/new"

            className="rounded-xl bg-[#172033] px-5 py-3 text-center text-sm font-bold text-white hover:bg-blue-600"

          >

            Submit resource

          </Link>

        </div>

        <div className="mt-8 flex flex-col gap-3 md:flex-row">

          <input

            value={search}

            onChange={(event) =>

              setSearch(event.target.value)

            }

            placeholder="Search resources..."

            className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

          />

          <select

            value={type}

            onChange={(event) =>

              setType(event.target.value)

            }

            className="rounded-xl border border-slate-300 px-4 py-3 text-sm"

          >

            {types.map((item) => (

              <option key={item} value={item}>

                {item}

              </option>

            ))}

          </select>

        </div>

        <div className="mt-5 flex flex-wrap gap-2">

          {categories.map((item) => (

            <button

              key={item}

              onClick={() => setCategory(item)}

              className={`rounded-full px-4 py-2 text-xs font-bold ${

                category === item

                  ? "bg-[#172033] text-white"

                  : "bg-slate-100 text-slate-600"

              }`}

            >

              {item}

            </button>

          ))}

        </div>

        {loading ? (

          <div className="py-20 text-center text-slate-500">

            Loading resources...

          </div>

        ) : (

          <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((resource) => (
              <Link

                key={resource.id}

                href={`/resources/${resource.slug}`}

                className="group rounded-2xl border border-slate-200 p-6 transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"

              >

                <div className="flex items-center justify-between">

                  <span className="rounded-lg bg-blue-50 px-3 py-1 text-xs font-bold text-blue-600">

                    {resource.resource_type}

                  </span>

                  <span className="text-xs text-slate-400">

                    {resource.downloads} downloads

                  </span>

                </div>

                <h2 className="mt-5 text-xl font-black text-[#172033] group-hover:text-blue-600">

                  {resource.title}

                </h2>

                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500">

                  {resource.description}

                </p>

                <div className="mt-6 text-xs font-bold text-blue-600">

                  {resource.category}

                </div>

              </Link>

            ))}

          </div>

        )}

      </main>

    </div>

  );

}