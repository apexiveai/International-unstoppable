"use client";

import Link from "next/link";

import { useEffect, useMemo, useState } from "react";

import SiteHeader from "@/components/SiteHeader";

import {

  getProjects,

  Project,

} from "@/lib/api";

const categories = [

  "All",

  "Artificial Intelligence",

  "AI Infrastructure",

  "Legal Technology",

  "Construction Technology",

  "Community",

];

export default function ProjectsPage() {

  const [projects, setProjects] = useState<Project[]>([]);

  const [search, setSearch] = useState("");

  const [category, setCategory] = useState("All");

  const [loading, setLoading] = useState(true);

  useEffect(() => {

    getProjects()

      .then(setProjects)

      .finally(() => setLoading(false));

  }, []);

  const filteredProjects = useMemo(() => {

    const query = search.trim().toLowerCase();

    return projects.filter((project) => {

      const categoryMatch =

        category === "All" ||

        project.category === category;

      const searchMatch =

        !query ||

        project.name.toLowerCase().includes(query) ||

        project.description.toLowerCase().includes(query);

      return categoryMatch && searchMatch;

    });

  }, [projects, search, category]);

  return (

    <div className="min-h-screen bg-white">

      <SiteHeader />

      <main className="mx-auto max-w-7xl px-6 py-12">

        <div className="flex flex-col gap-6 md:flex-row md:items-end">

          <div className="flex-1">

            <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">

              Build

            </p>

            <h1 className="mt-3 text-4xl font-black text-[#172033]">

              Projects

            </h1>

            <p className="mt-4 max-w-2xl text-slate-500">

              Discover products, open projects and ambitious

              technology ideas built by the community.

            </p>

          </div>

          <Link

            href="/projects/new"

            className="rounded-xl bg-[#172033] px-5 py-3 text-center text-sm font-bold text-white hover:bg-blue-600"

          >

            Submit a project

          </Link>

        </div>

        <div className="mt-8">

          <input

            value={search}

            onChange={(event) =>

              setSearch(event.target.value)

            }

            placeholder="Search projects..."

            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"

          />

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

            Loading projects...

          </div>

        ) : (

          <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">

            {filteredProjects.map((project) => (

              <Link

                key={project.id}

                href={`/projects/${project.slug}`}

                className="group rounded-2xl border border-slate-200 p-6 transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"

              >

                <div className="flex items-center justify-between">

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">

                    {project.status}

                  </span>

                  <span className="text-xs font-bold text-slate-400">

                    ★ {project.stars}

                  </span>

                </div>
                  <h2 className="mt-6 text-xl font-black text-[#172033] group-hover:text-blue-600">

                  {project.name}

                </h2>

                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500">

                  {project.description}

                </p>

                <div className="mt-6 text-xs font-bold text-blue-600">

                  {project.category}

                </div>

              </Link>

            ))}

          </div>

        )}

      </main>

    </div>

  );

}